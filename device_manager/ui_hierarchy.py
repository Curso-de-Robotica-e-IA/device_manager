from collections.abc import Callable
from typing import Any, Protocol

from device_manager.utils.adb_parsers import extract_ui_hierarchy_xml


class UiHierarchyBackend(Protocol):
    """Pluggable backend for capturing Android UI hierarchy XML."""

    def dump_xml(self, comm_uri: str) -> str | None:
        """Return the current `<hierarchy>` XML for `comm_uri`, or `None`."""
        ...


class Uiautomator2Backend:
    """Optional high-speed UI hierarchy backend powered by `uiautomator2`.

    Maintains a cached `u2.connect(comm_uri)` session per device so repeated
    `get_screen_gui_xml()` calls avoid Android's `uiautomator dump` cold start
    and 1-second `waitForIdle` floor (~150 ms vs ~2.4–3.5 s).
    """

    def __init__(
        self,
        connector: Callable[[str], Any] | None = None,
    ) -> None:
        self._connector = connector
        self._devices: dict[str, Any] = {}

    def _get_device(self, comm_uri: str) -> Any:
        device = self._devices.get(comm_uri)
        if device is None:
            connector = self._connector
            if connector is None:
                try:
                    import uiautomator2 as u2  # noqa: PLC0415
                except ImportError as exc:
                    raise ImportError(
                        'uiautomator2 is required for Uiautomator2Backend. '
                        'Install it with: pip install "device_manager[u2]"'
                    ) from exc
                connector = u2.connect
            device = connector(comm_uri)
            self._devices[comm_uri] = device
        return device

    def dump_xml(self, comm_uri: str) -> str | None:
        """Dump the current UI hierarchy XML using the cached `u2` session."""
        device = self._get_device(comm_uri)
        raw_xml = device.dump_hierarchy()
        if not raw_xml:
            return None
        return extract_ui_hierarchy_xml(str(raw_xml))
