import asyncio
import logging
import subprocess
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Sequence
from weakref import finalize

import qrcode
from qrcode.image.base import BaseImage
from zeroconf import InterfaceChoice, IPVersion, ServiceBrowser, Zeroconf

from device_manager.asyncio_dm.async_mdns_listener import AsyncMDnsListener
from device_manager.asyncio_dm.async_zeroconf import AsyncZeroconf
from device_manager.connection.adb_pairing import AdbPairing
from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import PAIRING_SERVICE_TYPE
from device_manager.utils.qrcode import QRCode
from device_manager.utils.util_functions import create_password

InterfacesType = (
    Sequence[str | int | tuple[tuple[str, int, int], int]] | InterfaceChoice
)

logger = logging.getLogger(__name__)


class AsyncAdbPairing:
    """Asynchronous ADB pairing service using composition instead of inheriting
    synchronous `AdbPairing` methods (preserving Liskov Substitution Principle).
    """

    def __init__(
        self,
        service_name: str = 'robot-celular',
        service_regex_filter: str | None = None,
        subprocess_check_flag: bool = False,
        password: str | None = None,
        max_zeroconf_instances: int = 10,
    ) -> None:
        self._name = service_name
        self._passwd = password if password is not None else create_password()
        self._qrcode = QRCode(
            qrcode_data=AdbPairing.generate_qrcode_string(
                service_name=self._name,
                password=self._passwd,
            )
        )
        self._service_re_filter = service_regex_filter
        self._service_type = PAIRING_SERVICE_TYPE
        self._zeroconf: AsyncZeroconf | None = None
        self._context = MDnsContext()
        self._started = False
        self._subprocess_check_flag = subprocess_check_flag
        self._browser: ServiceBrowser | None = None
        self._finalize: finalize[Any, Any] | None = None
        self._max_zc_instances = max_zeroconf_instances
        self._zeroconf_zombies: list[AsyncZeroconf] = []

    @property
    def service_browser_started(self) -> bool:
        return self._started

    @property
    def browser(self) -> ServiceBrowser | None:
        return self._browser

    @property
    def zeroconf_status(self) -> bool:
        if self._finalize is None:
            return False
        return self._finalize.alive

    @property
    def qrcode_string(self) -> str:
        return AdbPairing.generate_qrcode_string(self._name, self._passwd)

    @property
    def password(self) -> str:
        return self._passwd

    @property
    def qrcode(self) -> qrcode.QRCode[Any]:
        return self._qrcode.qrcode_object

    @property
    def qrcode_image(self) -> BaseImage:
        return self._qrcode.qr_image

    def update_qrcode(self, new_password: bool = False) -> None:
        if new_password:
            self._passwd = create_password()
        self._qrcode = QRCode(qrcode_data=self.qrcode_string)

    def set_password(self, password: str, update_qrcode: bool = True) -> None:
        self._passwd = password
        if update_qrcode:
            self.update_qrcode(new_password=False)

    def has_device_to_pairing(self) -> bool:
        return len(self._context.get_online_service()) > 0

    def _new_zeroconf_instance(
        self,
        interfaces: InterfacesType = InterfaceChoice.Default,
        unicast: bool = False,
        ip_version: IPVersion | None = None,
    ) -> None:
        if len(self._zeroconf_zombies) <= self._max_zc_instances:
            if self._zeroconf is not None:
                self._zeroconf_zombies.append(self._zeroconf)
                self._zeroconf = None
            raw_zc = Zeroconf(
                interfaces=interfaces,
                unicast=unicast,
                ip_version=ip_version,
                apple_p2p=False,
            )
            self._zeroconf = AsyncZeroconf(zc=raw_zc)

    async def start(
        self,
        interfaces: InterfacesType = InterfaceChoice.Default,
        unicast: bool = False,
        ip_version: IPVersion | None = None,
    ) -> None:
        """Start the asynchronous ServiceBrowser to listen for pairing services."""
        if not self._started:
            self._new_zeroconf_instance(
                interfaces=interfaces,
                unicast=unicast,
                ip_version=ip_version,
            )
            if self._zeroconf is None:
                raise AttributeError('zeroconf not configured')
            try:
                self._browser = ServiceBrowser(
                    self._zeroconf,  # type: ignore[arg-type]
                    self._service_type,
                    AsyncMDnsListener(
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

            self._finalize = finalize(self._zeroconf, atexit)
            self._started = True
            self._browser._async_start()  # pyright: ignore[reportPrivateUsage]
            await asyncio.sleep(5)

    async def stop_pair_listener(self) -> None:
        """Stop the ServiceBrowser and close the AsyncZeroconf instance."""
        if self._zeroconf is None:
            raise AttributeError('zeroconf not configured')
        await self._zeroconf.async_close()
        self._browser = None
        self._started = False

    async def pair_devices(self) -> bool:
        """Attempts to pair asynchronously with all discovered online devices."""
        online_services = list(self._context.get_online_service().items())
        if not online_services:
            return False

        all_ops: list[bool] = []
        for elem in online_services:
            comm_uri = f'{elem[1].ip}:{elem[1].port}'
            process = await asyncio.create_subprocess_exec(
                'adb',
                'pair',
                comm_uri,
                self._passwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_bytes, stderr_bytes = await process.communicate()
            stdout = stdout_bytes.decode(errors='replace')
            if self._subprocess_check_flag and process.returncode != 0:
                raise subprocess.CalledProcessError(
                    returncode=process.returncode or 1,
                    cmd=['adb', 'pair', comm_uri, self._passwd],
                    output=stdout,
                    stderr=stderr_bytes.decode(errors='replace'),
                )
            paired = f'Successfully paired to {comm_uri}' in stdout
            if paired:
                logger.info(
                    'Successfully paired device asynchronously: uri=%s',
                    comm_uri,
                )
            else:
                logger.warning(
                    'Failed to pair device asynchronously: uri=%s output=%s',
                    comm_uri,
                    stdout.strip(),
                )
            all_ops.append(paired)

        return all(all_ops)

    @asynccontextmanager
    async def pair(
        self,
        max_attempts: int = 3,
    ) -> AsyncGenerator[str, None]:
        """Async context manager that starts listening, yields QR string, and pairs."""
        try:
            await self.start()
            yield self.qrcode_string
        finally:
            success = False
            attempts = 0
            while not success and attempts < max_attempts:
                success = await self.pair_devices()
                attempts += 1
            await self.stop_pair_listener()
