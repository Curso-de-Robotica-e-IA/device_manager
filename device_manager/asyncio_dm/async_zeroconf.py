from typing import Any

from zeroconf.asyncio import AsyncZeroconf as AZc


class AsyncZeroconf:
    """Explicit Proxy/Adapter around `zeroconf.asyncio.AsyncZeroconf` that
    exposes underlying `Zeroconf` attributes cleanly via `__getattr__` without
    fragile multiple inheritance.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._azc = AZc(*args, **kwargs)

    @property
    def zeroconf(self) -> Any:
        return self._azc.zeroconf

    async def async_get_service_info(
        self,
        type_: str,
        name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        return await self._azc.async_get_service_info(
            type_,
            name,
            *args,
            **kwargs,
        )

    async def async_close(self) -> None:
        await self._azc.async_close()

    def __getattr__(self, name: str) -> Any:
        try:
            return getattr(self._azc, name)
        except AttributeError:
            return getattr(self._azc.zeroconf, name)
