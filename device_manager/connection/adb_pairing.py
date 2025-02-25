import secrets
import string
import subprocess
from contextlib import contextmanager
from typing import Generator, Optional
from weakref import finalize

import cv2 as cv
import numpy as np
import qrcode
from qrcode.main import GenericImage
from zeroconf import ServiceBrowser, Zeroconf

from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import (
    PAIRING_SERVICE_TYPE,
    MDnsListener,
)


class AdbPairing:
    """Class to pair the devices using the mDNS listener. It uses the Zeroconf
    library to listen to the mDNS services, and the MDnsListener class to
    update the service context with the service information found by the
    Zeroconf
    instance.

    Properties:
        - `service_browser_started` (bool): Check if the ServiceBrowser has
            been started.
        - `browser` (Optional[ServiceBrowser]): The actual ServiceBrowser
            instance.
        - `zeroconf_status` (bool): Check if the Zeroconf instance is active.
        - `qrcode_string` (str): Get the qrcode string.
        - `qrcode` (qrcode.QRCode): Get the qrcode object.
        - `qrcode_image` (qrcode.image.base.BaseImage): Get the qrcode image.

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
    """

    def __init__(
        self,
        service_name: str = 'robot-celular',
        service_regex_filter: Optional[str] = None,
        subprocess_check_flag: bool = False,
    ) -> None:
        self.__name = service_name
        self.__qr = None
        self.__qr_image = None
        self.__passwd = self.__create_password()
        self.__qrcode()
        self.__service_re_filter = service_regex_filter
        self.__service_type = PAIRING_SERVICE_TYPE
        self.__zeroconf: Optional[Zeroconf] = None
        self.__context = MDnsContext()
        self.__started = False
        self.__subprocess_check_flag = subprocess_check_flag
        self.__browser: Optional[ServiceBrowser] = None
        self.__finalize: Optional[finalize] = None

    @property
    def service_browser_started(self) -> bool:
        """Check if the ServiceBrowser has been started.

        Returns:
            bool: True if the ServiceBrowser has been started, False otherwise.
        """
        return self.__started

    @property
    def browser(self) -> Optional[ServiceBrowser]:
        """Returns the actual ServiceBrowser instance, if it exists.

        Returns:
            ServiceBrowser: The ServiceBrowser instance.
        """
        return self.__browser

    @property
    def zeroconf_status(self) -> bool:
        """Check if the Zeroconf instance is active.

        Returns:
            bool: True if the Zeroconf instance is active, False otherwise.
        """
        if self.__finalize is None:
            return False
        return self.__finalize.alive

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
        return f'WIFI:T:ADB;S:{self.__name};P:{self.__passwd};;'

    @property
    def qrcode(self) -> qrcode.QRCode:
        """Get the qrcode object.

        Returns:
            qrcode.QRCode: The qrcode object.
        """
        return self.__qr

    @property
    def qrcode_image(self) -> GenericImage:
        """Get the qrcode image.

        Returns:
            GenericImage: The qrcode image.
        """
        return self.__qr_image

    @staticmethod
    def __create_password() -> str:
        """Create a random password.
        The password is a string with 8 characters. The characters are
        alphanumeric.

        Returns:
            str: The password.
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(8))

    def __qrcode(self) -> None:
        """Create the qrcode image.
        The qrcode image is generated using the qrcode library. The qrcode
        string is generated using the method `qrcode_string`.
        """
        s = self.qrcode_string
        self.__qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=2,
        )
        self.__qr.add_data(s)
        self.__qr_image = self.__qr.make_image(
            fill_color='black',
            back_color='white',
        )

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
            self.__passwd = self.__create_password()
        self.__qrcode()

    def start(self) -> None:
        """Start the ServiceBrowser to listen to the mDNS services."""
        if not self.__started:
            self.__zeroconf = Zeroconf()
            self.__browser = ServiceBrowser(
                self.__zeroconf,
                self.__service_type,
                MDnsListener(
                    self.__context,
                    self.__service_re_filter,
                    self.__service_type,
                ),
            )

            def atexit() -> None:
                """Callback function to update the __started attribute and
                the __browser attribute, once the Zeroconf service has been
                finalized."""
                print('Zeroconf finalized')
                self.__browser = None
                self.__started = False

            self.__finalize = finalize(
                self.__zeroconf,
                atexit,
            )
            self.__started = True

    def qrcode_prompt_show(self) -> None:
        """Show the qrcode in the terminal."""
        self.__qr.print_ascii(tty=True)

    def qrcode_cv_window_show(self) -> None:
        """Show the qrcode in a window, using the openCV library.
        It expects the user to close the window to continue the execution of
        the script.
        """
        cv.imshow('pair', self.__get_img_cv())
        cv.waitKey(0)
        cv.destroyAllWindows()

    def __get_img_cv(self) -> cv.typing.MatLike:
        """Get the qrcode image in a format that can be used by the openCV
        library.

        Returns:
            cv.typing.MatLike: The qrcode image in a format that can be used by
                the openCV library.
        """
        img_rgb = self.__qr_image.convert('RGB')
        img_mat = cv.cvtColor(np.array(img_rgb), cv.COLOR_RGB2BGR)

        return cv.resize(img_mat, (400, 400))

    def has_device_to_pairing(self) -> bool:
        """Check if there are devices to pair.

        Returns:
            bool: True if there are devices to pair, False otherwise.
        """
        return len(self.__context.get_online_service()) > 0

    def pair_devices(self) -> bool:
        """Attempts to pair with the devices found by the mDNS listener.
        This method uses the adb command to pair with the devices. The
        connection URI is extracted from the service information found by the
        mDNS listener. That being said, it is necessary that the mDNS listener
        has been started before calling this method.

        Returns:
            bool: True if the pairing was successful, False otherwise.
        """
        success = False
        online_services = self.__context.get_online_service().items()
        for elem in online_services:
            comm_uri = f'{elem[1].ip}:{elem[1].port}'
            result = subprocess.run(
                ['adb', 'pair', comm_uri, self.__passwd],
                capture_output=True,
                text=True,
                check=self.__subprocess_check_flag,
            )
            if f'Successfully paired to {comm_uri}' in result.stdout:
                success = True

        return success

    def stop_pair_listener(self) -> None:
        """Stop the ServiceBrowser and close the Zeroconf instance."""
        self.__zeroconf.close()

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
