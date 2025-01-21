import subprocess
from connection.connection_manager import ConnectionManager
from connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from connection.components.manager import ObjectManager
from connection.utils.mdns_context import (
    ServiceInfo,
)
from rich import print
from rich.console import Console
from rich.prompt import Prompt
from time import sleep
from typing import List


class DeviceConnection:
    def __init__(self):
        self.console = Console()
        self.connection = ConnectionManager()
        self.connection_info: ObjectManager[ServiceInfo] = ObjectManager()

    def close(self):
        """
         This method terminates any ongoing device discovery process managed by
        the `connection_manager`. It ensures that resources related to device
        discovery are released properly.
        """

        self.connection.close_discovery()

    def check_connections(self) -> bool:
        """
        This method checks the status of the current connections and returns
        True if all devices are connected and updated. If any device is not
        connected or updated, the method returns False.

        Returns:
            bool: True if all devices are connected and updated, False
                otherwise.
        """

        devices_connected = subprocess.run(
            'adb devices',
            capture_output=True,
            text=True,
        ).stdout
        self.console.print(devices_connected)
        for serial_number in self.connection_info:
            device = self.connection_info.get(serial_number)
            substr = f'{device.ip}:{device.port}\tdevice'
            if substr not in devices_connected:
                return False
        return True

    def build_comm_uri(self, serial_number: str) -> str:
        """
        This method constructs a communication URI for the specified device
        using the IP address and port number stored in the `connection_info`
        attribute.

        Args:
            serial_number (str): The serial number of the device to connect to.

        Returns:
            str: The communication URI in the format `ip:port`.
        """

        device = self.connection_info.get(serial_number)
        return f"{device.ip}:{device.port}"

    def validate_connection(self, serial_number: str) -> bool:
        """
        This method checks whether a device is currently connected by
        evaluating the `connection_info` attribute. If no device is connected,
        it initiates the connection process. If a device is connected but its
        status is not updated or the connection is lost, it attempts to
        reconnect. The method handles cases where the device is offline or
        requires a reconnection.

        Returns:
            bool: True if the connection is valid or successfully
                reestablished.
        """

        if self.connection_info.get(serial_number) is None:
            print("Running without device connected")
            return self.start_connection()

        device = self.connection_info.get(serial_number)
        comm_uri = f"{device.ip}:{device.port}"

        if self.connection.check_wireless_adb_service_for(
                self.connection_info.get(serial_number),
        ) != ConnectionInfoStatus.UPDATED or not self.connection.check_devices_adb_connection(comm_uri):  # noqa

            if (
                    self.connection.check_wireless_adb_service_for(
                        self.connection_info.get(serial_number),
                    ) == ConnectionInfoStatus.DOWN
            ):
                print("Current device to offline")
                return self.start_connection()

            print("try update connection ...")
            connection = self.connection.device_connect(
                device.serial_number,
            )
            if connection is None:
                print("Connection failed, retry..")
                sleep(5)
                connection = self.connection.device_connect(
                    device.serial_number,
                )
            else:
                self.connection_info.edit(device.serial_number, connection)

            if connection is None:
                print("Connection lost")
                print("Running without device connected")
                return self.start_connection()
            else:
                print("Reconnection success!")

        return True

    def check_pairing(self) -> None:
        """Checks if a device is already paired with the host.
        Case it is not, it calls the `ConnectionManager` to pair the device.
        """
        prompt = Prompt()
        options = ['Y', 'N']
        response = prompt.ask(
            "Device already paired with host?",
            choices=options,
            case_sensitive=False,
        )
        paired = False if response.upper() == 'N' else True

        if not paired:
            self.console.print("Scan QRCode to pair and close window")
            if self.connection.device_pairing(5):
                print("Success in pairing new host!")
            else:
                print("Failed in pairing new host!")

    def select_devices_to_connect(self) -> List[str]:
        """Prompts the user to select devices to connect to.

        Returns:
            List[str]: A list of serial numbers of the devices selected by the
                user.
        """
        prompt = Prompt()

        device_idx = None
        finish_loop = False
        available_devices = self.connection.available_devices()
        selected_devices = list()
        while not finish_loop:
            prompt_options = {
                str(i+1): f"{srnmb} on IP: {available_devices[srnmb].ip}"
                for i, srnmb in enumerate(available_devices)
            }
            self.console.print("Available devices found in the network:")
            for key, prompt_msg in prompt_options.items():
                self.console.print(f"  [{key}] - {prompt_msg}")
            options = list(prompt_options.keys())
            options.append('0')
            response = prompt.ask(
                'Select device index to connect, or 0 to search devices again',
                choices=options,
            )

            if response == '0':
                available_devices = self.connection.available_devices()
            else:
                device_idx = int(response) - 1
                device = list(available_devices.keys())[device_idx]
                selected_devices.append(device)

                connect_another = prompt.ask(
                    'Do you want to connect to another device?',
                    choices=['Y', 'N'],
                    case_sensitive=False,
                )
                if connect_another == 'N':
                    finish_loop = True

        return selected_devices

    def establish_first_connection(self, device_serial_number: str) -> bool:
        """Attempts to establish an ADB connection with the specified device.

        Args:
            device_serial_number (str): The serial number of the device to
                connect to.

        Returns:
            bool: True if the connection is successfully established, False
                otherwise.
        """
        success = False
        connection = None
        for _ in range(3):
            if not success:
                self.console.print("Trying to connect ...")
                connection = self.connection.device_connect(
                    device_serial_number,
                )

            if connection is not None:
                success = True
            else:
                print(
                    f"ADB Connection for device {device_serial_number} failed",
                )

        if connection is not None:
            if self.connection_info.get(device_serial_number) is not None:
                self.connection_info.remove(device_serial_number)
            self.connection_info.add(connection.serial_number, connection)
            if self.connection_info.get(connection.serial_number).port != 5555:
                self.__fix_adb_port(connection.serial_number)
            return True

    def connect_all_devices(self) -> None:
        """"""
        for serial_number in self.connection_info:
            self.__connect_with_fix_port(serial_number)

    def start_connection(self) -> bool:
        """
        This method facilitates the process of connecting to an Android device
        by prompting the user for authorization and pairing if necessary. It
        lists available devices, allows the user to select one, and attempts to
        establish an ADB connection. The method will handle up to three
        connection attempts before failing.
        :return: True if the connection is successfully established,
            False otherwise.
        """
        self.check_pairing()

        selected_devices = self.select_devices_to_connect()

        for selected_serial_num in selected_devices:
            self.establish_first_connection(selected_serial_num)
        self.disconnect()
        self.connect_all_devices()
        return self.check_connections()

    def __fix_adb_port(self, serial_number: str):
        """Fix the ADB port by setting it to 5555.

        This method validates the current connection and if valid, runs the
        ADB command to set the device's port to 5555.
        """

        if self.validate_connection(serial_number):
            comm_uri = self.build_comm_uri(serial_number)
            subprocess.run(f"adb -s {comm_uri} tcpip 5555")
            self.connection_info.get(serial_number).port = 5555

    def __connect_with_fix_port(self, serial_number: str):
        """Reconnect using the fixed ADB port.

        This method establishes a new ADB connection using the fixed port
        (5555).
        """
        device = self.connection_info.get(serial_number)
        subprocess.run(f"adb connect {device.ip}:5555")

    @staticmethod
    def disconnect():
        """
        This method checks the device connection and executes an ADB command to
        kill the ADB server, effectively disconnecting the current session with
        the specified device.
        """
        subprocess.run("adb kill-server")
