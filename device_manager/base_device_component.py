from functools import wraps
from subprocess import CompletedProcess
from typing import Any, Callable, TypeVar

from device_manager.adb_executor import execute_adb_command
from device_manager.adb_gateway import AdbGateway
from device_manager.connection.device_connection import DeviceConnection
from device_manager.exceptions.errors import DeviceDisconnectedError

F = TypeVar('F', bound=Callable[..., Any])


def require_connection(
    *,
    raise_on_disconnect: bool = False,
    error_message: str = 'Device connection is not valid.',
) -> Callable[[F], F]:
    """Decorator enforcing connection validation before executing a method."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
            if not self.validate_connection():
                if raise_on_disconnect:
                    raise DeviceDisconnectedError(error_message)
                return None
            return func(self, *args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


class BaseDeviceComponent:
    """Base component providing shared connection resolution and ADB execution
    template methods for device-scoped services (DeviceActions, DeviceInfo,
    CameraActions, AppInfo).
    """

    def __init__(
        self,
        device_connection: DeviceConnection,
        serial_number: str,
        subprocess_check_flag: bool = False,
        gateway: AdbGateway | None = None,
    ) -> None:
        self.subprocess_check_flag = subprocess_check_flag
        self.device_connection = device_connection
        self._serial_number = serial_number
        self._gateway = gateway

    @property
    def serial_number(self) -> str:
        """The serial number associated with the device."""
        return self._serial_number

    @property
    def current_comm_uri(self) -> str:
        """The current communication URI for the device, resolved dynamically."""
        return self.device_connection.build_comm_uri(self._serial_number)

    def validate_connection(self) -> bool:
        """Validates the connection to the device."""
        return self.device_connection.validate_connection(
            self._serial_number,
            force_reconnect=False,
        )

    def _run_adb(
        self,
        command: str,
        *,
        shell: bool = True,
        capture_output: bool = False,
    ) -> CompletedProcess[str]:
        """Template helper to execute an ADB command targeting this device."""
        return execute_adb_command(
            command=command,
            comm_uris=[self.current_comm_uri],
            shell=shell,
            subprocess_check_flag=self.subprocess_check_flag,
            capture_output=capture_output,
            gateway=self._gateway,
        )
