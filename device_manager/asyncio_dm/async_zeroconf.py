from zeroconf.asyncio import AsyncZeroconf as AZc


class AsyncZeroconf(AZc):
    """AsyncZeroconf class to inherit from the Asynchronous implementation of
    the Zeroconf class provided by the zeroconf library. Since the
    AsyncServiceBrowser class requires attributes not directly available in
    the AsyncZeroconf class, this class inherits from the AsyncZeroconf class
    and provides the necessary attributes.
    """

    def __getattribute__(self, name: str):
        """__getattribute__ method to get the attribute from the Zeroconf
        instance if it does not exist in the AsyncZeroconf instance.
        """
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return self.zeroconf.__getattribute__(name)
