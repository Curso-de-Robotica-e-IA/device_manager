import subprocess
from time import sleep, time
from device.connection.adb_connection_discovery import AdbConnectionDiscovery
from device.connection.adb_pairing import AdbPairing
from device.connection.utils.service_info import ServiceInfo


class ConnectionManager:
    # Connection Manager has been developed based in to code available on https://github.com/openatx/adbutils/issues/111#issuecomment-2094694894
    def __init__(self) -> None:
        self.__discovery = AdbConnectionDiscovery()
        subprocess.run("adb start-server")
        self.__discovery.start()
        sleep(2)

    @staticmethod
    def check_devices_adb_connection(comm_uri):
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        devices_lines = str(result.stdout).split("\n")
        for info_line in devices_lines:
            if comm_uri in info_line and not ("offline" in info_line):

                return True

        return False

    def available_devices(self):

        return self.__discovery.list_of_online_device()

    @staticmethod
    def device_pairing(timeout_s):
        adb_pairing = AdbPairing()
        adb_pairing.start()
        adb_pairing.qrcode_cv_window_show()
        start_time = time()
        while (
            not adb_pairing.has_device_to_pairing()
            and (time() - start_time) <= timeout_s
        ):
            sleep(0.1)
        result = adb_pairing.pair_devices()
        adb_pairing.stop_pair_listener()

        return result

    def device_connect(self, serial_num):
        info = self.__discovery.get_service_info_for(serial_num)
        if info is None:
            print("Device service not online or located")
        else:
            comm_uri = f"{info.ip}:{info.port}"
            result = subprocess.run(
                ["adb", "connect", comm_uri], capture_output=True, text=True
            )
            if f"failed to connect to {comm_uri}" in result.stdout:
                print("Fail to connect device")
            elif self.check_devices_adb_connection(comm_uri):

                return info

    def check_wireless_adb_service_for(self, info):

        return self.__discovery.connection_status_for_device(info)

    def validate_and_reconnect_device(self, info: ServiceInfo):
        comm_uri = f"{info.ip}:{info.port}"
        if self.check_devices_adb_connection(comm_uri):

            return info

        return self.device_connect(info.serial_number)

    def close_discovery(self):
        self.__discovery.stop_discovery_listener()
