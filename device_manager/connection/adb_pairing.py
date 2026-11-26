import logging
import subprocess
from contextlib import contextmanager
from typing import Any, Generator, Sequence

import qrcode
from qrcode.image.base import BaseImage
from zeroconf import InterfaceChoice, IPVersion, ServiceBrowser

from device_manager.adb_gateway import AdbGateway, resolve_gateway
from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import PAIRING_SERVICE_TYPE
from device_manager.connection.utils.mdns_session import MdnsBrowserSession
from device_manager.utils.qrcode import QRCode
from device_manager.utils.util_functions import create_password

InterfacesType = (
    Sequence[str | int | tuple[tuple[str, int, int], int]] | InterfaceChoice
)
GenericImage = BaseImage

logger = logging.getLogger(__name__)


class AdbPairing:
    """Class to pair devices using mDNS discovery via `MdnsBrowserSession`
    composition and `AdbGateway` injection.
    """

    @staticmethod
    def generate_qrcode_string(service_name: str, password: str) -> str:
        """Generate the qrcode string using the service name and password."""
        return f'WIFI:T:ADB;S:{service_name};P:{password};;'

    def __init__(
        self,
        service_name: str = 'robot-celular',
        service_regex_filter: str | None = None,
        subprocess_check_flag: bool = False,
        password: str | None = None,
        max_zeroconf_instances: int = 10,
        gateway: AdbGateway | None = None,
        session: MdnsBrowserSession | None = None,
    ) -> None:
        self._name = service_name
        self._passwd = password if password is not None else create_password()
        self._qrcode = QRCode(
            qrcode_data=self.generate_qrcode_string(
                service_name=self._name,
                password=self._passwd,
            )
        )
        self._context = MDnsContext()
        self._subprocess_check_flag = subprocess_check_flag
        self._gateway = gateway
        self._session = (
            session
            if session is not None
            else MdnsBrowserSession(
                context=self._context,
                service_type=PAIRING_SERVICE_TYPE,
                service_re_filter=service_regex_filter,
                max_zeroconf_instances=max_zeroconf_instances,
            )
        )

    @property
    def service_browser_started(self) -> bool:
        return self._session.started

    @property
    def browser(self) -> ServiceBrowser | None:
        return self._session.browser

    @property
    def zeroconf_status(self) -> bool:
        return self._session.zeroconf_status

    @property
    def qrcode_string(self) -> str:
        return self.generate_qrcode_string(self._name, self._passwd)

    @property
    def password(self) -> str:
        return self._passwd

    @property
    def qrcode(self) -> qrcode.QRCode[Any]:
        return self._qrcode.qrcode_object

    @property
    def qrcode_image(self) -> GenericImage:
        return self._qrcode.qr_image

    def update_qrcode(self, new_password: bool = False) -> None:
        if new_password:
            self._passwd = create_password()
        self._qrcode = QRCode(qrcode_data=self.qrcode_string)

    def set_password(self, password: str, update_qrcode: bool = True) -> None:
        self._passwd = password
        if update_qrcode:
            self.update_qrcode(new_password=False)

    def start(
        self,
        interfaces: InterfacesType = InterfaceChoice.All,
        unicast: bool = False,
        ip_version: IPVersion | None = None,
    ) -> None:
        """Start the ServiceBrowser via `MdnsBrowserSession`."""
        self._session.start(
            interfaces=interfaces,
            unicast=unicast,
            ip_version=ip_version,
        )

    def has_device_to_pairing(self) -> bool:
        return len(self._context.get_online_service()) > 0

    def _get_gateway(self) -> AdbGateway:
        return resolve_gateway(self._gateway, subprocess.run)

    def pair_devices(self) -> bool:
        """Attempts to pair with the devices found by the mDNS listener."""
        online_services = list(self._context.get_online_service().items())
        if not online_services:
            return False

        gateway = self._get_gateway()
        all_ops: list[bool] = []
        for elem in online_services:
            comm_uri = f'{elem[1].ip}:{elem[1].port}'
            result = gateway.run(
                ['adb', 'pair', comm_uri, self._passwd],
                capture_output=True,
                text=True,
                check=self._subprocess_check_flag,
            )
            paired = f'Successfully paired to {comm_uri}' in result.stdout
            if paired:
                logger.info('Successfully paired device: uri=%s', comm_uri)
            else:
                logger.warning(
                    'Failed to pair device: uri=%s output=%s',
                    comm_uri,
                    result.stdout.strip(),
                )
            all_ops.append(paired)

        return all(all_ops)

    def stop_pair_listener(self) -> None:
        """Stop the ServiceBrowser and close the Zeroconf instance."""
        self._session.stop()

    @contextmanager
    def pair(self, max_attempts: int = 3) -> Generator[str, None, None]:
        """Context manager that starts listening, yields QR string, and pairs."""
        try:
            self.start()
            yield self.qrcode_string
        finally:
            success = False
            attempts = 0
            while not success and attempts < max_attempts:
                success = self.pair_devices()
                attempts += 1
            self.stop_pair_listener()

    def pair_device_with_paring_code(
        self,
        comm_uri: str,
        pair_code: str,
    ) -> bool:
        result = self._get_gateway().run(
            ['adb', 'pair', comm_uri, pair_code],
            capture_output=True,
            text=True,
            check=self._subprocess_check_flag,
        )
        success = f'Successfully paired to {comm_uri}' in result.stdout
        if success:
            logger.info(
                'Successfully paired device with code: uri=%s', comm_uri
            )
        else:
            logger.warning(
                'Failed to pair device with code: uri=%s output=%s',
                comm_uri,
                result.stdout.strip(),
            )
        return success
