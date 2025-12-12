import logging
import subprocess
from typing import List, Optional

from device_manager.connection.connection_manager import (
    ConnectionManagerSingleton,
)


logger = logging.getLogger(__name__)


class DeviceConnection:
    """This class is responsible for managing the connection with devices.
    It provides methods to establish, validate, and close connections with
    devices. It also provides methods to check the status of the current
    connections and to build communication URIs for the devices.

    Args:
        subprocess_check_flag (bool, optional): A flag to check if the
                subprocess execution was successful, passed to the subprocess
                `check` argument. Defaults to False.
                Check the subprocess documentation for more information.

    Attributes:
        connection (ConnectionManager): A connection manager to manage the
            ADB connections.

    methods:

        list_all_devices: Lists all devices connected via USB.
        connected_devices: Lists all currently connected devices.
        check_authorization: Checks if a device is authorized for ADB
        validate_connection: Validates the current connection with the
            specified device.
    """

    def __init__(
        self,
        subprocess_check_flag: bool = False,
    ):
        self.__subprocess_check_flag = subprocess_check_flag
        self.connection = ConnectionManagerSingleton(
            subprocess_check_flag=self.__subprocess_check_flag,
        )

    def validate_connection(
        self,
        serial_number: str,
        devices_connected: Optional[str] = None,
    ) -> bool:
        """Check if the device is connected to the host.

        Args:
            serial_number (str): The serial number of the device to check.

        Returns:
            bool: True if the device is connected, False otherwise.
        """
        if devices_connected is None:
            devices_connected = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                check=self.__subprocess_check_flag,
            ).stdout

        substr = f'{serial_number}\tdevice'

        result = False
        if substr in devices_connected:
            result = True
        return result
    
    def list_all_devices(self) -> List[str]:
        """
        This method lists all devices connected via USB and returns a list of
        their serial numbers.

        Returns:
            List[str]: A list of serial numbers of devices connected via USB.
        """
        devices_connected = subprocess.run(
        ['adb', 'devices'],
        capture_output=True,
        text=True,
        check=self.__subprocess_check_flag,
        ).stdout

        usb_serial_numbers = {}

        for line in devices_connected.splitlines()[1:]:
            line = line.strip()

            if line:
                serial = line.split("\t")[0]
                status = line.split("\t")[1]

                if serial.isalnum():
                    usb_serial_numbers[serial] = status

        return usb_serial_numbers
    
    def connected_devices(self) -> List[str]:
        """
        This method checks for devices connected via USB and returns a list of
        their serial numbers.

        Returns:
            List[str]: A list of serial numbers of devices connected via USB.
        """
        devices_connected = subprocess.run(
        ['adb', 'devices'],
        capture_output=True,
        text=True,
        check=self.__subprocess_check_flag,
        ).stdout

        usb_serial_numbers = []

        for line in devices_connected.splitlines()[1:]:
            line = line.strip()

            if line.endswith("\tdevice"):
                serial = line.split("\t")[0]

                if serial.isalnum():
                    usb_serial_numbers.append(serial)

        return usb_serial_numbers

    def check_authorization(self, serial_number: str) -> bool:
        """
        This method checks if the device with the given serial number is
        authorized for ADB communication.

        Args:
            serial_number (str): The serial number of the device to check.

        Returns:
            bool: True if the device is authorized, False otherwise.
        """
        devices_connected = subprocess.run(
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            check=self.__subprocess_check_flag,
        ).stdout

        for line in devices_connected.splitlines()[1:]:
            line = line.strip()

            if line.startswith(serial_number):
                if "unauthorized" in line:
                    return False
                elif "device" in line:
                    return True

        return False
