from typing import Any

import qrcode
import qrcode.constants
from qrcode.image.base import BaseImage


class QRCode:
    """Pure QR code generator (data + image). Presentation concerns live in
    `device_manager.cli.qrcode_viewer.QRCodeViewer` (SRP).
    """

    def __init__(
        self,
        qrcode_data: str,
        fill_color: str = 'black',
        back_color: str = 'white',
    ) -> None:
        self.__qrcode_data = qrcode_data
        self.__fill_color = fill_color
        self.__back_color = back_color
        self._rebuild_qrcode()

    def _rebuild_qrcode(self) -> None:
        self.__object = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=2,
        )
        self.__object.add_data(self.__qrcode_data)
        self.__qr_image = self.__object.make_image(
            fill_color=self.__fill_color,
            back_color=self.__back_color,
        )

    @property
    def qrcode_string(self) -> str:
        return self.__qrcode_data

    @qrcode_string.setter
    def qrcode_string(self, value: Any) -> None:
        if not isinstance(value, str):
            raise TypeError('The QR code data must be a string.')
        self.__qrcode_data = value
        self._rebuild_qrcode()

    @property
    def qrcode_object(self) -> qrcode.QRCode[Any]:
        return self.__object

    @property
    def qr_image(self) -> BaseImage:
        return self.__qr_image
