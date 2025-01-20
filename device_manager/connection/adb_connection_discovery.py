import weakref
from zeroconf import ServiceBrowser, Zeroconf
from device_manager.connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from device_manager.connection.utils.mdns_context import (
    MDnsContext,
    ServiceInfo,
)
from device_manager.connection.utils.mdns_listener import MDnsListener


class AdbConnectionDiscovery:

    def __init__(self):
        self.__started = False
        self.__service_re_filter = "adb\-(\w+)\-\w+\\"
        self.__service_type = "_adb-tls-connect._tcp.local."
        self.__zeroconf = None
        self.__finalize = None
        self.__browser = None
        self.__context = MDnsContext()

    def start(self):
        if not self.__started:
            self.__zeroconf = Zeroconf()
            self.__browser = ServiceBrowser(
                self.__zeroconf,
                self.__service_type,
                MDnsListener(
                    self.__context,
                    self.__service_re_filter,
                    self.__service_type,
                ),
            )

            def atexit(zeroconf):
                zeroconf.close()
            self.__finalize = weakref.finalize(
                self.__zeroconf,
                atexit,
                self.__zeroconf,
            )
            self.__started = True

    def list_of_online_device(self):

        return self.__context.get_online_service_list()

    def list_of_offline_device(self):

        return self.__context.get_offline_service_list()

    def get_service_info_for(self, serial_num: str) -> ServiceInfo | None:
        services_data = self.__context.get_online_service_list()
        if serial_num in services_data:

            return services_data[serial_num]

    def connection_status_for_device(
        self, service_info: ServiceInfo
    ) -> ConnectionInfoStatus:
        if service_info.serial_number in self.__context.get_offline_service_list():  # noqa

            return ConnectionInfoStatus.DOWN

        if service_info.serial_number not in self.__context.get_online_service_list():  # noqa

            return ConnectionInfoStatus.UNKNOWN

        services_data = self.__context.get_online_service_list()
        service_ref = services_data[service_info.serial_number]

        if service_ref.ip == service_info.ip:

            return ConnectionInfoStatus.UPDATED

        return ConnectionInfoStatus.CHANGED

    def stop_discovery_listener(self):
        self.__zeroconf.close()
