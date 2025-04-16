import logging
import subprocess
from contextlib import contextmanager
from typing import Generator, List, Optional, Sequence, Tuple, Union
from weakref import finalize

import qrcode
from qrcode.main import GenericImage
from zeroconf import InterfaceChoice, IPVersion, ServiceBrowser, Zeroconf

from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import (
    PAIRING_SERVICE_TYPE,
    MDnsListener,
)
from device_manager.utils.qrcode import QRCode
from device_manager.utils.util_functions import create_password

InterfacesType = Union[
    Sequence[Union[str, int, Tuple[Tuple[str, int, int], int]]],
    InterfaceChoice,
]  # noqa

logger = logging.getLogger(__name__)


class AdbPairing:
    """Class to pair the devices using the mDNS listener. It uses the Zeroconf
    library to listen to the mDNS services, and the MDnsListener class to
    update the service context with the service information found by the
    Zeroconf
    instance.

    Args:
        service_name (str, optional): The service name to listen to. Defaults
            to 'robot-celular'.
        service_regex_filter (Optional[str], optional): The regex filter to
            apply to the service name. Defaults to None.
        subprocess_check_flag (bool, optional): Indicates if the subprocess
            must raise an exception if the command fails. Defaults to False.
        password (Optional[str], optional): The password to pair the devices.
            If None, a random password is generated. Defaults to None.
        max_zeroconf_instances (int, optional): The max number of Zeroconf
            instances that can be created. Defaults to 10.

    Properties:
        - `service_browser_started` (bool): Check if the ServiceBrowser has
            been started.
        - `browser` (Optional[ServiceBrowser]): The actual ServiceBrowser
            instance.
        - `zeroconf_status` (bool): Check if the Zeroconf instance is active.
        - `qrcode_string` (str): Get the qrcode string.
        - `qrcode` (qrcode.QRCode): Get the qrcode object.
        - `qrcode_image` (qrcode.image.base.BaseImage): Get the qrcode image.
        - `password` (str): Get the password.

    Methods:
        update_qrcode: Update the qrcode image.
        start: Start the ServiceBrowser to listen to the mDNS services.
        qrcode_prompt_show: Show the qrcode in the terminal.
        qrcode_cv_window_show: Show the qrcode in a window, using the openCV
            library.
        pair_devices: Attempts to pair with the devices found by the mDNS
            listener.
        stop_pair_listener: Stop the ServiceBrowser and close the Zeroconf
            instance.
        pair: Pair the devices using the mDNS listener.

    Class Methods:
        generate_qrcode_string: Generate the qrcode string using the service
            name and password.
    """

    @staticmethod
    def generate_qrcode_string(service_name: str, password: str) -> str:
        """Generate the qrcode string using the service name and password.

        Args:
            service_name (str): The service name.
            password (str): The password.

        Returns:
            str: The qrcode string.
        """
        return f'WIFI:T:ADB;S:{service_name};P:{password};;'

    def __init__(
        self,
        service_name: str = 'robot-celular',
        service_regex_filter: Optional[str] = None,
        subprocess_check_flag: bool = False,
        password: Optional[str] = None,
        max_zeroconf_instances: int = 10,
    ) -> None:
        self._name = service_name
        if password is not None:
            self._passwd = password
        else:
            self._passwd = create_password()
        self._qrcode = QRCode(
            qrcode_data=self.generate_qrcode_string(
                service_name=self._name,
                password=self._passwd,
            )
        )
        self._service_re_filter = service_regex_filter
        self._service_type = PAIRING_SERVICE_TYPE
        self._zeroconf: Optional[Zeroconf] = None
        self._context = MDnsContext()
        self._started = False
        self._subprocess_check_flag = subprocess_check_flag
        self._browser: Optional[ServiceBrowser] = None
        self._finalize: Optional[finalize] = None
        self._max_zc_instances = max_zeroconf_instances
        self._zeroconf_zombies: List[Zeroconf] = list()

    @property
    def service_browser_started(self) -> bool:
        """Check if the ServiceBrowser has been started.

        Returns:
            bool: True if the ServiceBrowser has been started, False otherwise.
        """
        return self._started

    @property
    def browser(self) -> Optional[ServiceBrowser]:
        """Returns the actual ServiceBrowser instance, if it exists.

        Returns:
            ServiceBrowser: The ServiceBrowser instance.
        """
        return self._browser

    @property
    def zeroconf_status(self) -> bool:
        """Check if the Zeroconf instance is active.

        Returns:
            bool: True if the Zeroconf instance is active, False otherwise.
        """
        if self._finalize is None:
            return False
        return self._finalize.alive

    @property
    def qrcode_string(self) -> str:
        """Get the qrcode string.
        The qrcode string is a string that contains the information to generate
        a qrcode. The string is in the format
        "WIFI:T:ADB;S:{service_name};P:{password};;".
        Where:
           `WIFI:T:ADB` represents that the pairing session is for an ADB
              connection.
            `S:{service_name}` represents the service name.
            `P:{password}` represents the password to pair the devices.

        Returns:
            str: The qrcode string.
        """
        return self.generate_qrcode_string(self._name, self._passwd)

    @property
    def password(self) -> str:
        """Get the password.

        Returns:
            str: The password.
        """
        return self._passwd

    @property
    def qrcode(self) -> qrcode.QRCode:
        """Get the qrcode object.

        Returns:
            qrcode.QRCode: The qrcode object.
        """
        return self._qrcode.qrcode_object

    @property
    def qrcode_image(self) -> GenericImage:
        """Get the qrcode image.

        Returns:
            GenericImage: The qrcode image.
        """
        return self._qrcode.qr_image

    def update_qrcode(self, new_password: bool = False) -> None:
        """Update the qrcode image.
        The qrcode image is updated using the qrcode library. The qrcode
        string is updated using the method `qrcode_string`.

        Args:
            new_password (bool, optional): Indicates that a new password must
                be generated before the new QRCode is created.
                Defaults to False.
        """
        if new_password:
            self._passwd = create_password()
        self._qrcode = QRCode(qrcode_data=self.qrcode_string)

    def set_password(self, password: str, update_qrcode: bool = True) -> None:
        """Explicitly sets the internal password attribute, and updates the
        qrcode values.

        Args:
            password (str): The new password.
            update_qrcode (bool, optional): Indicates that the qrcode image
                must be updated. Defaults to True.
        """
        self._passwd = password
        if update_qrcode:
            self.update_qrcode(new_password=False)

    def _new_zeroconf_instance(
        self,
        interfaces: InterfacesType = InterfaceChoice.Default,
        unicast: bool = False,
        ip_version: Optional[IPVersion] = None,
    ) -> None:
        """Creates a new Zeroconf instance and appends the old instance to the
        __zeroconf_zombies list, if the list is not full (defined by the
        __max_zc_instances attribute)

        Args:
            interfaces (InterfacesType, optional): The interfaces to listen to.
                Defaults to InterfaceChoice.Default.
            unicast (bool, optional): Indicates if the mDNS listener should
                listen to unicast packets. Defaults to False.
            ip_version (Optional[IPVersion], optional): The IP version to use.
                Defaults to None.
        """
        if len(self._zeroconf_zombies) <= self._max_zc_instances:
            if self._zeroconf is not None:
                self._zeroconf_zombies.append(self._zeroconf)
                self._zeroconf = None
            self._zeroconf = Zeroconf(
                interfaces=interfaces,
                unicast=unicast,
                ip_version=ip_version,
                apple_p2p=False,
            )

    def start(
        self,
        interfaces: InterfacesType = InterfaceChoice.Default,
        unicast: bool = False,
        ip_version: Optional[IPVersion] = None,
    ) -> None:
        """Start the ServiceBrowser to listen to the mDNS services.
        This functions accepts the interfaces, unicast, and ip_version
        arguments to pass to the Zerocof constructor.

        If the Zeroconf instance is None, a new instance is created. The
        ServiceBrowser is created with the Zeroconf instance and the
        MDnsListener instance. The Zeroconf instance is finalized when the
        ServiceBrowser is finalized.

        If you manually call this method, you must call the
        `stop_pair_listener` method to stop the ServiceBrowser and close the
        Zeroconf instance.

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
                interfaces=interfaces, unicast=unicast, ip_version=ip_version
            )
            try:
                self._browser = ServiceBrowser(
                    self._zeroconf,
                    self._service_type,
                    MDnsListener(
                        self._context,
                        self._service_re_filter,
                        self._service_type,
                    ),
                )
            except RuntimeError as e:
                # Keeps the traceback, but explains what happened
                raise RuntimeError(
                    'Maximum number of Zeroconf instances reached.'
                ) from e

            def atexit() -> None:
                """Callback function to update the __started attribute and
                the __browser attribute, once the Zeroconf service has been
                finalized."""
                logger.debug('Finalizing Zeroconf instance.')
                self._browser = None
                self._started = False

            self._finalize = finalize(
                self._zeroconf,
                atexit,
            )
            self._started = True

    def has_device_to_pairing(self) -> bool:
        """Check if there are devices to pair.

        Returns:
            bool: True if there are devices to pair, False otherwise.
        """
        return len(self._context.get_online_service()) > 0

    def pair_devices(self) -> bool:
        """Attempts to pair with the devices found by the mDNS listener.
        This method uses the adb command to pair with the devices. The
        connection URI is extracted from the service information found by the
        mDNS listener. That being said, it is necessary that the mDNS listener
        has been started before calling this method.

        Returns:
            bool: True if the pairing was successful, False otherwise.
        """
        online_services = list(self._context.get_online_service().items())
        all_ops = list()
        for elem in online_services:
            comm_uri = f'{elem[1].ip}:{elem[1].port}'
            result = subprocess.run(
                ['adb', 'pair', comm_uri, self._passwd],
                capture_output=True,
                text=True,
                check=self._subprocess_check_flag,
            )
            if f'Successfully paired to {comm_uri}' in result.stdout:
                all_ops.append(True)
            else:
                all_ops.append(False)

        if len(all_ops) == 0:
            return False

        return all(all_ops)

    def stop_pair_listener(self) -> None:
        """Stop the ServiceBrowser and close the Zeroconf instance."""
        self._zeroconf.close()
        self._browser = None
        self._started = False

    @contextmanager
    def pair(self, max_attempts: int = 3) -> Generator[str, None, None]:
        """Pair the devices using the mDNS listener. This method is a context
        manager that starts the mDNS listener, shows the qrcode, and tries to
        pair the devices. It yields the qrcode string and waits for the devices
        to be paired. The context manager stops the mDNS listener after the
        block is executed.

        Args:
            max_attempts (int, optional): The max number of retry attempts to
                detect the pair proccess. Defaults to 3.

        Returns:
            str: The qrcode string.

        Yields:
            Generator[str, None, None]: The qrcode string.
        """

        def coro():
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

        c = coro()
        yield next(c)
