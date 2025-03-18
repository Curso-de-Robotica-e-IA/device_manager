from device_manager.asyncio.async_zeroconf import AsyncZeroconf
from device_manager.connection.utils.mdns_listener import MDnsListener


class AsyncMDnsListener(MDnsListener):
    """Asynchronous implementation of the MDnsListener.
    """

    async def update_service(
        self,
        zc: AsyncZeroconf,
        type_: str,
        name: str,
    ) -> None:
        """Updates the service information in the service context.

        Args:
            zc (AsyncZeroconf): AsyncZeroconf instance.
            type_ (str): The service type.
            name (str): The name of the service.
        """
        zcinfo = await zc.async_get_service_info(type_, name)
        info = self._extract_info(zcinfo)
        if info:
            await self.__service_context.update_service(
                info.serial_number,
                info,
            )

    async def remove_service(
        self,
        zc: AsyncZeroconf,
        type_: str,
        name: str,
    ):
        """Removes the service information from the service context.

        Args:
            zc (AsyncZeroconf): AsyncZeroconf instance.
            type_ (str): The service type.
            name (str): The name of the service.
        """
        zcinfo = await zc.async_get_service_info(type_, name)
        info = self._extract_info(zcinfo)
        if info:
            await self.__service_context.to_offline_service(
                info.serial_number,
                info,
            )

    async def add_service(
        self,
        zc: AsyncZeroconf,
        type_: str,
        name: str,
    ):
        """Adds the service information to the service context.

        Args:
            zc (AsyncZeroconf): AsyncZeroconf instance.
            type_ (str): The service type.
            name (str): The name of the service.
        """
        zcinfo = await zc.async_get_service_info(type_, name)
        info = self._extract_info(zcinfo)
        if info:
            await self.__service_context.add_service(
                info.serial_number,
                info,
                )
