

import subprocess
from typing import Optional

from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.connection.utils.service_type import ServiceType


class UsbDeviceScanner:
    def __init__(self, subprocess_check_flag):
        self.__subprocess_check_flag = subprocess_check_flag

    def list_all_devices(self) -> dict[str, str]:
        connected_devices = subprocess.run(
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            check=self.__subprocess_check_flag,
        ).stdout

        usb_serial_numbers = {}

        for line in connected_devices.splitlines()[1:]:
            striped_line = line.strip()

            if striped_line:
                serial = striped_line.split('\t')[0]
                status = striped_line.split('\t')[1]
                if serial.isalnum():
                    usb_serial_numbers[serial] = status

        return usb_serial_numbers

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
    
    def list_connected_devices(self) -> list[ServiceInfo]:
        """
        This method checks for devices connected and authorized via USB and
        returns a list of their serial numbers.

        Returns:
            List[str]: A list of serial numbers of devices connected via USB.
        """
        connected_devices = subprocess.run(
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            check=self.__subprocess_check_flag,
        ).stdout

        usb_serial_numbers = []

        for line in connected_devices.splitlines()[1:]:
            striped_line = line.strip()

            if striped_line.endswith('\tdevice'):
                serial = striped_line.split('\t')[0]

                if serial.isalnum():
                    usb_serial_numbers.append(ServiceInfo(
                        serial_number=serial,
                        ip="",
                        port=0,
                        connection=ConnectionType.USB,
                        service_type=ServiceType.CONNECT
                    )
                )

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
        connected_devices = subprocess.run(
            ['adb', 'devices'],
            capture_output=True,
            text=True,
            check=self.__subprocess_check_flag,
        ).stdout

        for line in connected_devices.splitlines()[1:]:
            striped_line = line.strip()

            if striped_line.startswith(serial_number):
                if 'unauthorized' in striped_line:
                    return False
                elif 'device' in striped_line:
                    return True

        return False