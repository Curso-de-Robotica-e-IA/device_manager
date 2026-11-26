from threading import Event, Lock

from device_manager.connection.utils.service_info import ServiceInfo


class MDnsContext:
    """Thread-safe store for online/offline mDNS services with an Event for
    non-polling readiness waits.
    """

    def __init__(self) -> None:
        self.__services_info_online: dict[str, ServiceInfo] = {}
        self.__services_info_offline: dict[str, ServiceInfo] = {}
        self.__mutex = Lock()
        self.__online_event = Event()

    def wait_for_online_service(self, timeout: float | None = None) -> bool:
        """Block until at least one service is online or timeout expires."""
        return self.__online_event.wait(timeout=timeout)

    @property
    def online_service_list(self) -> list[ServiceInfo]:
        return list(self.get_online_service().values())

    def get_online_service(self) -> dict[str, ServiceInfo]:
        with self.__mutex:
            return self.__services_info_online.copy()

    @property
    def offline_service_list(self) -> list[ServiceInfo]:
        return list(self.get_offline_service().values())

    def get_offline_service(self) -> dict[str, ServiceInfo]:
        with self.__mutex:
            return self.__services_info_offline.copy()

    def add_service(self, key_data: str, data: ServiceInfo) -> None:
        with self.__mutex:
            self.__services_info_offline.pop(key_data, None)
            self.__services_info_online[key_data] = data
            self.__online_event.set()

    def to_offline_service(self, key_data: str, data: ServiceInfo) -> None:
        with self.__mutex:
            self.__services_info_online.pop(key_data, None)
            self.__services_info_offline[key_data] = data
            if not self.__services_info_online:
                self.__online_event.clear()
