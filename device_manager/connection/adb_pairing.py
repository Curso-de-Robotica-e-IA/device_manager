import logging
import subprocess
from typing import Optional

from device_manager.connection.adb_connection_discovery import AdbConnectionDiscovery
from device_manager.connection.utils.mdns_context import MDnsContext

logger = logging.getLogger(__name__)


class AdbPairing:
    """Class responsible for managing the ADB pairing process with devices discovered via mDNS.

    Args:
        subprocess_check_flag (bool, optional): Indicates if the subprocess
            must raise an exception if the command fails. Defaults to False.

    Methods:
            has_device_to_pairing: Checks if there are devices to pair.
            pair_devices: Attempts to pair with the devices found by the mDNS
                listener.

    """

    def __init__(
        self,
        context: Optional[MDnsContext] = None,
        subprocess_check_flag: bool = False,
        ) -> None:
        self.connection_dicovery = AdbConnectionDiscovery()
        self._context = context
        self._subprocess_check_flag = subprocess_check_flag


    def has_device_to_pairing(self) -> bool:
        """Check if there are devices to pair.

        Returns:
            bool: True if there are devices to pair, False otherwise.
        """
        return len(self._context.pairing_services) > 0

    def pair_devices(self, pair_code: str) -> dict[str, bool]:
        """Attempts to pair with the devices found by the mDNS listener.
        This method uses the adb command to pair with the devices. The
        connection URI is extracted from the service information found by the
        mDNS listener. That being said, it is necessary that the mDNS listener
        has been started before calling this method.

        Returns:
            dict[str, bool]: A dictionary mapping connection URIs to pairing success status.
        """
        online_services = self._context.pairing_services
        all_ops = dict()
        for elem in online_services:
            comm_uri = f'{elem.ip}:{elem.port}'
            result = subprocess.run(
                ['adb', 'pair', comm_uri, pair_code],
                capture_output=True,
                text=True,
                check=self._subprocess_check_flag,
            )
            if f'Successfully paired to {comm_uri}' in result.stdout:
                all_ops[comm_uri] = True
            else:
                all_ops[comm_uri] = False
        if len(all_ops) == 0:
            return False

        return all_ops


if __name__ == "__main__":
    adb_pair = AdbPairing()
    success = adb_pair.pair_devices("052535")
    print(f"Pairing successful: {success}")

