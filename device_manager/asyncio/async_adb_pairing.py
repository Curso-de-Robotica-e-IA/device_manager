import asyncio
import logging
import subprocess
from typing import Optional, Sequence, Tuple, Union
from weakref import finalize

from zeroconf import InterfaceChoice, IPVersion, ServiceBrowser

from device_manager.asyncio.async_mdns_listener import AsyncMDnsListener
from device_manager.asyncio.async_zeroconf import AsyncZeroconf
from device_manager.connection.adb_pairing import AdbPairing

InterfacesType = Union[Sequence[Union[str, int, Tuple[Tuple[str, int, int], int]]], InterfaceChoice]  # noqa


logger = logging.getLogger(__name__)


class AsyncAdbPairing(AdbPairing):
    """AsyncAdbPairing class to pair with devices found by the mDNS listener.
    This class inherits from the AdbPairing class and provides an asynchronous
    implementation to pair with devices found by the mDNS listener.
    """

    def _new_zeroconf_instance(
        self,
        interfaces: InterfacesType = InterfaceChoice.Default,
        unicast: bool = False,
        ip_version: Optional[IPVersion] = None,
    ):
        """Instantiates a new AsyncZeroconf instance with the given arguments.
        It uses the base class Zeroconf instance to create the new
        asynchronous Zeroconf instance.

        Args:
            interfaces (InterfacesType, optional): The interfaces to listen to.
                Defaults to InterfaceChoice.Default.
            unicast (bool, optional): Indicates if the mDNS listener should
                listen to unicast packets. Defaults to False.
            ip_version (Optional[IPVersion], optional): The IP version to use.
                Defaults to None.
        """
        super()._new_zeroconf_instance(interfaces, unicast, ip_version)
        old_instance = self._zeroconf
        self._zeroconf = AsyncZeroconf(
            zc=old_instance,
        )

    async def start(
        self,
        interfaces: InterfacesType = InterfaceChoice.Default,
        unicast: bool = False,
        ip_version: Optional[IPVersion] = None,
    ) -> None:
        """Start the AsyncServiceBrowser to listen to the mDNS services.
        This functions accepts the interfaces, unicast, and ip_version
        arguments to pass to the Zerocof constructor.

        If the Zeroconf instance is None, a new instance is created. The
        AsyncServiceBrowser is created with the Zeroconf instance and the
        MDnsListener instance. The Zeroconf instance is finalized when the
        AsyncServiceBrowser is finalized.

        If you manually call this method, you must call the
        `stop_pair_listener` method to stop the AsyncServiceBrowser and close
        the Zeroconf instance.

        Args:
            interfaces (InterfacesType, optional): The interfaces to listen to.
                Defaults to InterfaceChoice.Default.
            unicast (bool, optional): Indicates if the mDNS listener should
                listen to unicast packets. Defaults to False.
            ip_version (Optional[IPVersion], optional): The IP version to use.
                Defaults to None.
        """
        if not self._started:
            self._new_zeroconf_instance(
                interfaces=interfaces,
                unicast=unicast,
                ip_version=ip_version,
            )
            try:
                self._browser = ServiceBrowser(
                    self._zeroconf,
                    self._service_type,
                    AsyncMDnsListener(
                        self._context,
                        self._service_re_filter,
                        self._service_type,
                    ),
                )
            except RuntimeError as e:
                raise RuntimeError(
                    'Maximum number of Zeroconf instances reached.') from e

            def atexit() -> None:
                logger.debug('Finalizing Zeroconf instance.')
                self._browser = None
                self._started = False

            self._finalize = finalize(self._zeroconf, atexit)
            self._started = True
            self._browser._async_start()
            asyncio.sleep(5)

    async def stop_pair_listener(self) -> None:
        """Stop the ServiceBrowser and close the Zerconf instance."""
        await self._zeroconf._async_close()
        self._browser = None
        self._started = False

    async def pair_devices(self) -> bool:
        """Attempts to pair with the devices found by the mDNS listener.
        This method uses the adb command to pair with the devices. The
        connection URI is extracted from the service information found by the
        mDNS listener. That being said, it is necessary that the mDNS listener
        has been started before calling this method.

        Returns:
            bool: True if the pairing was successful, False otherwise.
        """
        online_services = self._context.get_online_service().items()
        all_ops = [False] * len(online_services)
        for idx, elem in enumerate(online_services):
            comm_uri = f'{elem[1].ip}:{elem[1].port}'
            result = subprocess.run(
                ['adb', 'pair', comm_uri, self._passwd],
                capture_output=True,
                text=True,
                check=self._subprocess_check_flag,
            )
            if f'Successfully paired to {comm_uri}' in result.stdout:
                all_ops[idx] = True

        return all(all_ops)
