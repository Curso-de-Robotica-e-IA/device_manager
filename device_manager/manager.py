from components.manager import ObjectManager
from connection.device_connection import DeviceConnection
from device_actions import DeviceActions
from device_info import DeviceInfo
from typing import Tuple, Optional


class DeviceManager:

    def __init__(self):
        self.connector = DeviceConnection()
        self.__device_info: ObjectManager[DeviceInfo] = ObjectManager()
        self.__device_actions: ObjectManager[DeviceActions] = ObjectManager()

    def connect_devices(self, *serial_number: str) -> bool:
        """Connects to the devices with the provided serial numbers.
        This method will start the connection to the devices and create
        the necessary DeviceInfo and DeviceActions objects, which will be
        stored in the internal object manager objects.

        Returns:
            bool: True if the connection was successful, False otherwise.
        """
        serial_number_list = list(serial_number)
        success_op = self.connector.start_connection(serial_number_list)
        if success_op:
            for serial in self.connector.connection_info.keys():
                if serial not in self.__device_info.keys():
                    dev_info = DeviceInfo(
                        self.connector,
                        serial,
                    )
                    dev_actions = DeviceActions(
                        self.connector,
                        serial,
                    )
                    self.__device_info.add(serial, dev_info)
                    self.__device_actions.add(serial, dev_actions)
        return success_op

    def get_device_info(self, serial_number: str) -> DeviceInfo:
        """Retrieves the device information associated with a given
        serial number.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            DeviceInfo: The device information object.
        """
        return self.__device_info.get(serial_number)

    def get_device_actions(self, serial_number: str) -> DeviceActions:
        """Retrieves the device actions associated with a given serial number.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            DeviceActions: The device actions object.
        """
        return self.__device_actions.get(serial_number)

    def __getitem__(
        self,
        serial_number: str,
    ) -> Optional[Tuple[DeviceInfo, DeviceActions]]:
        """Get the device information and actions associated with a
        serial number. If the serial number is not found, None is returned.

        Args:
            serial_number (str): The serial number of the device.

        Returns:
            Optional[Tuple[DeviceInfo, DeviceActions]]: The device information
            and actions associated with the serial number.
        """
        try:
            info = self.__device_info.get(serial_number)
            actions = self.__device_actions.get(serial_number)
            return info, actions
        except KeyError:
            return None
