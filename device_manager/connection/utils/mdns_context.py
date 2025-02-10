from threading import Lock
from device_manager.connection.utils.service_info import ServiceInfo


class MDnsContext:
    def __init__(self):
        self.__services_info_online = {}
        self.__services_info_offline = {}
        self.__mutex = Lock()

    def get_online_service_list(self) -> dict[str, ServiceInfo]:
        with self.__mutex:
            all_data = self.__services_info_online

            return all_data

    def get_offline_service_list(self) -> dict[str, ServiceInfo]:
        with self.__mutex:
            all_data = self.__services_info_offline

            return all_data

    def add_service(self, key_data, data) -> None:
        with self.__mutex:
            if key_data in self.__services_info_offline:
                self.__services_info_offline.pop(key_data)
            self.__services_info_online[key_data] = data

    def update_service(self, key_data, data) -> None:
        with self.__mutex:
            if key_data in self.__services_info_offline:
                self.__services_info_offline.pop(key_data)
            self.__services_info_online[key_data] = data

    def to_offline_service(self, key_data, data) -> None:
        with self.__mutex:
            if key_data in self.__services_info_online:
                self.__services_info_online.pop(key_data)
            self.__services_info_offline[key_data] = data
