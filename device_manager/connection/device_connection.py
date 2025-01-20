import subprocess
from connection.connection_manager import ConnectionManager
from connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from rich import print
from rich.console import Console
from rich.prompt import Prompt
from time import sleep


class DeviceConnection:
    def __init__(self):
        self.console = Console()
        self.connection = ConnectionManager()
        self.connection_info = None
        self.current_comm_uri = None

    def close(self):
        """
         This method terminates any ongoing device discovery process managed by
        the `connection_manager`. It ensures that resources related to device
        discovery are released properly.
        """

        self.connection.close_discovery()

    def validate_connection(self) -> bool:
        """
        This method checks whether a device is currently connected by
        evaluating the `connection_info` attribute. If no device is connected,
        it initiates the connection process. If a device is connected but its
        status is not updated or the connection is lost, it attempts to
        reconnect. The method handles cases where the device is offline or
        requires a reconnection.
        :return: True if the connection is valid or successfully reestablished.
        """

        if self.connection_info is None:
            print("Running without device connected")
            return self.start_connection()

        comm_uri = f"{self.connection_info.ip}:{self.connection_info.port}"

        if self.connection.check_wireless_adb_service_for(
                self.connection_info
        ) != ConnectionInfoStatus.UPDATED or not self.connection.check_devices_adb_connection(comm_uri):  # noqa

            if (
                    self.connection.check_wireless_adb_service_for(
                        self.connection_info,
                    ) == ConnectionInfoStatus.DOWN
            ):
                print("Current device to offline")
                return self.start_connection()

            print("try update connection ...")
            connection = self.connection.device_connect(
                self.connection_info.serial_number,
            )
            if connection is None:
                print("Connection failed, retry..")
                sleep(5)
                connection = self.connection.device_connect(
                    self.connection_info.serial_number,
                )

            self.connection_info = connection
            if connection is None:
                self.current_comm_uri = None
                print("Connection lost")
                print("Running without device connected")
                return self.start_connection()
            else:
                print("Reconnection success!")
                self.current_comm_uri = f"{self.connection_info.ip}:{self.connection_info.port}"  # noqa

        else:
            self.current_comm_uri = comm_uri

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

        print("Available devices to connect:\n")
        device_idx = None
        while True:
            available_devices = self.connection.available_devices()
            for i, serial_number in enumerate(available_devices):
                print(f"[{i}] - {serial_number} on IP: {available_devices[serial_number].ip}")  # noqa

            device_idx = None
            while device_idx is None:
                res = input("Select device index to connect, or just press enter to search devices again: ")  # noqa
                if len(res) == 0:
                    device_idx = -1
                else:
                    int_res = None

                    try:
                        int_res = int(res)
                        if (
                            isinstance(int_res, int)
                            and int_res < len(available_devices)
                        ):
                            device_idx = int_res
                    except Exception as err:  # noqa
                        print(f'Error: {err}')

            if device_idx >= 0:
                break

        selected_serial_num = list(available_devices.keys())[device_idx]
        connection = None

        count = 0
        while count < 3:
            print("Try connect ...")
            connection = self.connection.device_connect(
                selected_serial_num,
            )

            if connection is None:
                print(f"Connection adb for device {selected_serial_num} failed")  # noqa
            else:
                print(f"Connection adb for device {selected_serial_num} success!")  # noqa
                break
            count += 1

        if connection is not None:
            self.connection_info = connection
            self.current_comm_uri = f"{self.connection_info.ip}:{self.connection_info.port}"  # noqa
            if self.connection_info.port != 5555:
                self.__change_adb_port()
                # Talvez tenha que dar um kill-server antes

            return True

    def __change_adb_port(self):
        """Change the ADB port and reconnect.

        This method calls `__fix_adb_port` to fix the ADB port, disconnects
        from the current connection, and then reconnects using the fixed port
        (5555).
        It updates the connection URI with the new port number.
        """

        self.__fix_adb_port()
        self.disconnect()
        self.__connect_with_fix_port()
        self.connection_info.port = 5555
        self.current_comm_uri = f"{self.connection_info.ip}:{self.connection_info.port}"  # noqa

    def __fix_adb_port(self):
        """Fix the ADB port by setting it to 5555.

        This method validates the current connection and if valid, runs the
        ADB command to set the device's port to 5555.
        """

        if self.validate_connection():
            subprocess.run(f"adb -s {self.current_comm_uri} tcpip 5555")

    def __connect_with_fix_port(self):
        """Reconnect using the fixed ADB port.

        This method establishes a new ADB connection using the fixed port
        (5555).
        """

        subprocess.run(f"adb connect {self.connection_info.ip}:5555")

    @staticmethod
    def disconnect():
        """
        This method checks the device connection and executes an ADB command to
        kill the ADB server, effectively disconnecting the current session with
        the specified device.
        """
        subprocess.run("adb kill-server")
