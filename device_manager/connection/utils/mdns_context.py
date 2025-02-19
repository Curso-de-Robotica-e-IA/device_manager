from threading import Lock
from typing import Dict

from device_manager.connection.utils.service_info import ServiceInfo


class MDnsContext:
    """Context to store the services found by the mDNS listener. It stores the
    services in two lists: online and offline, and uses a mutex to protect the
    data.

    Attributes:
        __services_info_online (Dict[str, ServiceInfo]): The online services.
        __services_info_offline (Dict[str, ServiceInfo]): The offline services.
        __mutex (Lock): The mutex to protect the data.

    Properties:
        online_service_list (Dict[str, ServiceInfo]): The online service list.
        offline_service_list (Dict[str, ServiceInfo]): The offline service
            list.

    Methods:
        get_online_service_list(): Get the online service list.
        get_offline_service_list(): Get the offline service list.
        add_service(key_data, data): Add a service to the online list.
        update_service(key_data, data): Update a service in the online list.
        to_offline_service(key_data, data): Move a service to the offline list.
    """
    def __init__(self):
        self.__services_info_online = {}
        self.__services_info_offline = {}
        self.__mutex = Lock()

    @property
    def online_service_list(self) -> Dict[str, ServiceInfo]:
        """Get the online service list.

        Returns:
            Dict[str, ServiceInfo]: The online service list.
        """
        return self.get_online_service_list()

    def get_online_service_list(self) -> Dict[str, ServiceInfo]:
        """Get the online service list.

        Returns:
            Dict[str, ServiceInfo]: The online service list.
        """
        with self.__mutex:
            all_data = self.__services_info_online

            return all_data

    @property
    def offline_service_list(self) -> Dict[str, ServiceInfo]:
        """Get the offline service list.

        Returns:
            Dict[str, ServiceInfo]: The offline service list.
        """
        return self.get_offline_service_list()

    def get_offline_service_list(self) -> Dict[str, ServiceInfo]:
        """Get the offline service list.

        Returns:
            Dict[str, ServiceInfo]: The offline service list.
        """
        with self.__mutex:
            all_data = self.__services_info_offline

            return all_data

    def add_service(
        self,
        key_data: str,
        data: ServiceInfo,
    ) -> None:
        """Add a service to the online list. If the service is already in the
        offline list, it will be removed from there.

        Args:
            key_data (str): The key to identify the service.
            data (ServiceInfo): The service data.
        """
        with self.__mutex:
            if key_data in self.__services_info_offline:
                self.__services_info_offline.pop(key_data)
            self.__services_info_online[key_data] = data

    def update_service(
        self,
        key_data: str,
        data: ServiceInfo,
    ) -> None:
        """Update a service in the online list. If the service is already in
        the offline list, it will be removed from there.

        Args:
            key_data (str): The key to identify the service.
            data (ServiceInfo): The service data.
        """
        with self.__mutex:
            if key_data in self.__services_info_offline:
                self.__services_info_offline.pop(key_data)
            self.__services_info_online[key_data] = data

    def to_offline_service(
        self,
        key_data: str,
        data: ServiceInfo,
    ) -> None:
        """Move a service to the offline list. If the service is already in the
        online list, it will be removed from there.

        Args:
            key_data (str): The key to identify the service.
            data (ServiceInfo): The service data.
        """
        with self.__mutex:
            if key_data in self.__services_info_online:
                self.__services_info_online.pop(key_data)
            self.__services_info_offline[key_data] = data
