from typing import List
from device_manager.connection.utils.mdns_service import MdnsService


class MDnsContext:
    """Snapshot of mDNS services discovered via adb.
    This class serves as a context for storing and managing the mDNS services
    discovered on the local network using the `adb mdns services` command. It
    provides methods to set and retrieve the list of services, as well as to
    filter services based on their type (online or pairing) and to get service
    information based on the serial number. The context is used to maintain the
    state of the discovered services and to facilitate access to this information
    for other components of the device manager.
        Attributes:
            _services (List[MdnsService]): A list of `MdnsService` instances representing the discovered services.
        Methods:
            set_services: Sets the list of discovered services in the context.
            services: Retrieves the list of all discovered services.
            online_services: Retrieves the list of services that are currently online.
            pairing_services: Retrieves the list of services that are available for pairing.
            get_by_serial: Retrieves the service information for a given serial number.
    """

    def __init__(self) -> None:
        self._services: List[MdnsService] = []

    def set_services(self, services: List[MdnsService]) -> None:
        """Sets the list of discovered services in the context.
        This method takes a list of `MdnsService` instances representing the
        discovered services and stores it in the context for later retrieval and
        management.
        
        Args:
            services (List[MdnsService]): A list of `MdnsService` instances representing the discovered services.
        Returns:
            None
        """ 
        self._services = services

    @property
    def services(self) -> List[MdnsService]:
        return self._services
    
    @property
    def online_services(self) -> List[MdnsService]:
        return [s for s in self._services if s.service_type == "ONLINE"]

    @property
    def pairing_services(self) -> List[MdnsService]:
        return [s for s in self._services if s.service_type == "PAIRING"]

    def get_by_serial(self, serial: str) -> MdnsService | None:
        """Retrieves the service information for a given serial number.
        This method searches through the list of discovered services to find a
        service that matches the provided serial number. If a matching service is
        found, it is returned; otherwise, the method returns `None`.
        
        Args:
            serial (str): The serial number of the service to retrieve.
        
        Returns:
            MdnsService | None: The `MdnsService` instance that matches the provided serial number, or `None` if no match is found.
        """
        for s in self._services:
            if s.serial_number == serial:
                return s
        return None

