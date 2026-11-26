import base64
import logging
from pathlib import Path
from typing import Any, Protocol

from device_manager.exceptions.errors import UnsupportedAndroidVersionError
from device_manager.utils.adb_parsers import extract_ui_hierarchy_xml

logger = logging.getLogger(__name__)

DEFAULT_DEX_PATH = Path(__file__).parent / 'assets' / 'dm_ui_dump.dex'
REMOTE_DEX_PATH = '/data/local/tmp/dm_ui_dump.dex'
SERVER_MAIN_CLASS = 'com.devicemanager.UiDumpServer'
END_TAG = '</hierarchy>'
MIN_RESIDENT_SDK = 21
DEFAULT_RESIDENT_TIMEOUT_S = 5.0


class UiHierarchyBackend(Protocol):
    """Pluggable backend for capturing Android UI hierarchy XML."""

    def dump_xml(self, comm_uri: str) -> str | None:
        """Return the current `<hierarchy>` XML for `comm_uri`, or `None`."""
        ...


class NativeResidentUiBackend:
    """Resident Android `app_process` backend for fast UI XML dumps (~12 ms).

    Pushes the bundled `dm_ui_dump.dex` (5.2 KB) to `/data/local/tmp` once per
    device and keeps a persistent `app_process` session open over an `adbutils`
    TCP socket. Each `dump_xml()` call sends `DUMP\\n` and reads `<hierarchy>`
    directly without Android's 1-second `waitForIdle`.
    """

    def __init__(
        self,
        dex_path: str | Path = DEFAULT_DEX_PATH,
        client: Any | None = None,
        timeout: float = DEFAULT_RESIDENT_TIMEOUT_S,
        min_sdk: int = MIN_RESIDENT_SDK,
    ) -> None:
        self._dex_path = Path(dex_path)
        self._client = client
        self._timeout = timeout
        self._min_sdk = min_sdk
        self._sessions: dict[str, Any] = {}

    def _get_client(self) -> Any:
        if self._client is None:
            import adbutils  # noqa: PLC0415

            self._client = adbutils.adb
        return self._client

    def _check_sdk_compatibility(self, device: Any, comm_uri: str) -> None:
        raw_sdk = str(device.shell('getprop ro.build.version.sdk')).strip()
        if raw_sdk.isdigit() and int(raw_sdk) < self._min_sdk:
            raise UnsupportedAndroidVersionError(
                f'Device {comm_uri} runs Android API {raw_sdk}, '
                f'below minimum API {self._min_sdk} required by dm_ui_dump.dex.'
            )

    def _ensure_session(self, comm_uri: str) -> Any:
        session = self._sessions.get(comm_uri)
        if session is not None:
            return session
        device = self._get_client().device(serial=comm_uri)
        self._check_sdk_compatibility(device, comm_uri)
        device.sync.push(str(self._dex_path), REMOTE_DEX_PATH)
        cmd = f'CLASSPATH={REMOTE_DEX_PATH} app_process / {SERVER_MAIN_CLASS}'
        conn = device.shell(cmd, stream=True)
        conn.conn.settimeout(self._timeout)
        self._sessions[comm_uri] = conn
        return conn

    def close(self, comm_uri: str | None = None) -> None:
        """Close one or all resident `app_process` stream sessions."""
        targets = (
            [comm_uri] if comm_uri is not None else list(self._sessions.keys())
        )
        for uri in targets:
            conn = self._sessions.pop(uri, None)
            if conn is not None:
                try:
                    conn.conn.sendall(b'QUIT\n')
                except Exception:  # noqa: S110
                    pass
                conn.close()

    def dump_xml(self, comm_uri: str) -> str | None:
        """Request an immediate XML dump from the resident `app_process`."""
        if not self._dex_path.exists():
            return None
        try:
            conn = self._ensure_session(comm_uri)
            conn.conn.sendall(b'DUMP\n')
            chunks: list[bytes] = []
            while True:
                data: bytes = conn.conn.recv(8192)
                if not data:
                    self.close(comm_uri)
                    return None
                chunks.append(data)
                joined = b''.join(chunks).decode('utf-8', errors='replace')
                if END_TAG in joined:
                    return extract_ui_hierarchy_xml(joined)
        except UnsupportedAndroidVersionError:
            raise
        except Exception:
            logger.debug(
                'NativeResidentUiBackend failed for %s.',
                comm_uri,
                exc_info=True,
            )
            self.close(comm_uri)
            return None

    @staticmethod
    def _recv_framed_image(sock: Any) -> str | None:
        chunks: list[bytes] = []
        while True:
            data: bytes = sock.recv(65536)
            if not data:
                return None
            chunks.append(data)
            joined = b''.join(chunks).decode('ascii', errors='ignore')
            if 'IMG_ERR' in joined:
                return 'ERR'
            end_idx = joined.find(':IMG_END')
            if end_idx != -1:
                start_idx = joined.find('IMG_BEGIN:')
                if start_idx != -1:
                    return joined[start_idx + len('IMG_BEGIN:') : end_idx]
                return None

    def take_screenshot(
        self,
        comm_uri: str,
        *,
        fmt: str = 'png',
    ) -> bytes | None:
        """Capture a PNG or JPEG screenshot via `UiAutomation.takeScreenshot()`."""
        if not self._dex_path.exists():
            return None
        try:
            conn = self._ensure_session(comm_uri)
            cmd = b'SCREENSHOT_JPEG\n' if fmt == 'jpeg' else b'SCREENSHOT\n'
            conn.conn.sendall(cmd)
            payload = self._recv_framed_image(conn.conn)
            if not payload or payload == 'ERR':
                if payload is None:
                    self.close(comm_uri)
                return None
            return base64.b64decode(payload)
        except UnsupportedAndroidVersionError:
            raise
        except Exception:
            logger.debug(
                'NativeResidentUiBackend.take_screenshot failed for %s.',
                comm_uri,
                exc_info=True,
            )
            self.close(comm_uri)
            return None

    def save_screenshot(self, comm_uri: str, remote_path: str) -> bool:
        """Save a JPEG screenshot directly to `remote_path` on the device."""
        if not self._dex_path.exists():
            return False
        try:
            conn = self._ensure_session(comm_uri)
            conn.conn.sendall(f'SCREENSHOT_FILE {remote_path}\n'.encode())
            chunks: list[bytes] = []
            while True:
                data: bytes = conn.conn.recv(4096)
                if not data:
                    self.close(comm_uri)
                    return False
                chunks.append(data)
                joined = b''.join(chunks).decode('ascii', errors='ignore')
                if 'FILE_OK' in joined:
                    return True
                if 'FILE_ERR' in joined:
                    return False
        except UnsupportedAndroidVersionError:
            raise
        except Exception:
            logger.debug(
                'NativeResidentUiBackend.save_screenshot failed for %s.',
                comm_uri,
                exc_info=True,
            )
            self.close(comm_uri)
            return False
