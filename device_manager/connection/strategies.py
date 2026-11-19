import logging
from typing import TYPE_CHECKING, Protocol

from device_manager.connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo

if TYPE_CHECKING:
    from device_manager.connection.device_connection import DeviceConnection

logger = logging.getLogger(__name__)


class ConnectionStrategy(Protocol):
    """Strategy interface for transport-specific ADB addressing, connection,
    and validation.
    """

    def build_comm_uri(self, service: ServiceInfo) -> str: ...

    def format_adb_device_entry(self, service: ServiceInfo) -> str: ...

    def connect(
        self,
        connector: 'DeviceConnection',
        serials: list[str],
    ) -> list[str]: ...

    def validate(
        self,
        connector: 'DeviceConnection',
        service: ServiceInfo,
        *,
        force_reconnect: bool = False,
    ) -> bool: ...


class UsbConnectionStrategy:
    """Strategy for USB-connected ADB devices."""

    def build_comm_uri(self, service: ServiceInfo) -> str:
        return service.serial_number

    def format_adb_device_entry(self, service: ServiceInfo) -> str:
        return f'{service.serial_number}\tdevice'

    def connect(
        self,
        connector: 'DeviceConnection',
        serials: list[str],
    ) -> list[str]:
        return [
            serial for serial in serials if connector.is_connected(serial)
        ]

    def validate(
        self,
        connector: 'DeviceConnection',
        service: ServiceInfo,
        *,
        force_reconnect: bool = False,
    ) -> bool:
        return connector.usb_scanner.validate_connection(service.serial_number)


class WifiConnectionStrategy:
    """Strategy for Wi-Fi (TCP/IP) ADB devices."""

    def build_comm_uri(self, service: ServiceInfo) -> str:
        return f'{service.ip}:{service.port}'

    def format_adb_device_entry(self, service: ServiceInfo) -> str:
        return f'{service.ip}:{service.port}\tdevice'

    def connect(
        self,
        connector: 'DeviceConnection',
        serials: list[str],
    ) -> list[str]:
        if not serials:
            return []
        return connector.start_connection(serials)

    def validate(
        self,
        connector: 'DeviceConnection',
        service: ServiceInfo,
        *,
        force_reconnect: bool = False,
    ) -> bool:
        comm_uri = self.build_comm_uri(service)
        coninfostatus = connector.connection.check_wireless_adb_service_for(
            service,
        )
        adb_connected = connector.connection.check_devices_adb_connection(
            comm_uri,
        )
        if coninfostatus != ConnectionInfoStatus.UPDATED or not adb_connected:
            if not force_reconnect:
                logger.debug(
                    'Wi-Fi validation failed (no reconnect): serial=%s uri=%s mdns_status=%s adb_connected=%s',
                    service.serial_number,
                    comm_uri,
                    coninfostatus.name,
                    adb_connected,
                )
                return False

            logger.warning(
                'Wi-Fi connection invalid; forcing ADB server reconnect: serial=%s uri=%s mdns_status=%s adb_connected=%s',
                service.serial_number,
                comm_uri,
                coninfostatus.name,
                adb_connected,
            )
            connector.establish_first_connection(service.serial_number)
            connector.disconnect()
            connector.connect_all_devices()

            return connector.validate_connection(
                service.serial_number,
                force_reconnect=False,
            )

        return True


_STRATEGIES: dict[ConnectionType, ConnectionStrategy] = {
    ConnectionType.USB: UsbConnectionStrategy(),
    ConnectionType.WIFI: WifiConnectionStrategy(),
}


def get_connection_strategy(
    connection_type: ConnectionType,
) -> ConnectionStrategy:
    """Returns the ConnectionStrategy registered for the given ConnectionType."""
    try:
        return _STRATEGIES[connection_type]
    except KeyError as exc:
        raise ValueError(
            f'Unsupported connection type: {connection_type}'
        ) from exc
