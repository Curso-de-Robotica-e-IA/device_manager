import re
import socket
from zeroconf import ServiceListener, Zeroconf
from connection.utils.mdns_context import ServiceInfo


class MDnsListener(ServiceListener):
    def __init__(self, service_context, re_filter, service_type) -> None:
        super().__init__()
        self.__service_context = service_context
        self.__re_filter = re_filter
        self.__type_filter = service_type

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = self.__extract_info(zc.get_service_info(type_, name))
        if info:
            self.__service_context.update_service(info.serial_number, info)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = self.__extract_info(zc.get_service_info(type_, name))
        if info:
            self.__service_context.to_offline_service(info.serial_number, info)

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = self.__extract_info(zc.get_service_info(type_, name))
        if info:
            self.__service_context.add_service(info.serial_number, info)

    def __extract_info(self, info) -> ServiceInfo | None:
        try:
            ip = f"{socket.inet_ntoa(info.addresses[0])}"
            port = info.port
            if self.__re_filter is None:
                return ServiceInfo(info.name.split(".")[0], ip, port)
            else:
                if m := re.match(
                    rf"{self.__re_filter}.{self.__type_filter}", info.name
                ):
                    serial_num = m.group(1)
                    return ServiceInfo(serial_num, ip, port)
                else:
                    print(f"AdbMDns not match: {info.name}")
        except Exception as e:
            print(e)
