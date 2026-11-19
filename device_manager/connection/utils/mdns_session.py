import logging
from typing import Any, Callable, Sequence
import weakref

from zeroconf import InterfaceChoice, IPVersion, ServiceBrowser, Zeroconf

from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import MDnsListener

InterfacesType = (
    Sequence[str | int | tuple[tuple[str, int, int], int]] | InterfaceChoice
)

logger = logging.getLogger(__name__)


class MdnsBrowserSession:
    """Reusable composition component managing Zeroconf & ServiceBrowser
    lifecycle, finalizers, and zombie instance tracking.
    """

    def __init__(
        self,
        context: MDnsContext,
        service_type: str,
        service_re_filter: str | None = None,
        max_zeroconf_instances: int = 10,
        zeroconf_factory: Callable[..., Zeroconf] | None = None,
        browser_factory: Callable[..., ServiceBrowser] | None = None,
    ) -> None:
        self._context = context
        self._service_type = service_type
        self._service_re_filter = service_re_filter
        self._max_zc_instances = max_zeroconf_instances
        self._zeroconf_factory = zeroconf_factory
        self._browser_factory = browser_factory
        self._zeroconf: Zeroconf | None = None
        self._browser: ServiceBrowser | None = None
        self._finalize: weakref.finalize[Any, Any] | None = None
        self._started = False
        self._zeroconf_zombies: list[Zeroconf] = []

    @property
    def started(self) -> bool:
        return self._started

    @property
    def browser(self) -> ServiceBrowser | None:
        return self._browser

    @property
    def zeroconf_status(self) -> bool:
        if self._finalize is None:
            return False
        return self._finalize.alive

    def start(
        self,
        interfaces: InterfacesType = InterfaceChoice.Default,
        unicast: bool = False,
        ip_version: IPVersion | None = None,
    ) -> None:
        if self._started:
            return
        if len(self._zeroconf_zombies) <= self._max_zc_instances:
            if self._zeroconf is not None:
                self._zeroconf_zombies.append(self._zeroconf)
                self._zeroconf = None
            zc_factory = self._zeroconf_factory or Zeroconf
            self._zeroconf = zc_factory(
                interfaces=interfaces,
                unicast=unicast,
                ip_version=ip_version,
                apple_p2p=False,
            )
        if self._zeroconf is None:
            raise AttributeError('Zeroconf not configured')
        try:
            browser_factory = self._browser_factory or ServiceBrowser
            self._browser = browser_factory(
                self._zeroconf,
                self._service_type,
                MDnsListener(
                    self._context,
                    self._service_re_filter,
                    self._service_type,
                ),
            )
        except RuntimeError as exc:
            raise RuntimeError(
                'Maximum number of Zeroconf instances reached.'
            ) from exc

        def atexit() -> None:
            logger.debug('Finalizing Zeroconf instance.')
            self._browser = None
            self._started = False

        self._finalize = weakref.finalize(self._zeroconf, atexit)
        self._started = True
        logger.debug('Started mDNS browser for service_type=%s', self._service_type)

    def stop(self) -> None:
        if self._zeroconf is None:
            raise AttributeError('ServiceBrowser not started')
        self._zeroconf.close()
        self._browser = None
        self._started = False
        logger.debug('Stopped mDNS browser for service_type=%s', self._service_type)
