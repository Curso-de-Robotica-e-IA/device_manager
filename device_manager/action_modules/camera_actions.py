from typing import Callable

from device_manager.connection.device_connection import DeviceConnection


class CameraActions:

    def __init__(
        self,
        device_connection: DeviceConnection,
        serial_number: str,
        subprocess_check_flag: bool,
        validate_connection_callback: Callable[[], bool] = lambda: True,
    ) -> None:
        self.device_connection = device_connection
        self.serial_number = serial_number
        self.subprocess_check_flag = subprocess_check_flag
        self.validate_connection_callback = validate_connection_callback
