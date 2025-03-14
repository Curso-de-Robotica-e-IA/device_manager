import cv2 as cv
import numpy as np
import qrcode
import qrcode.constants
from qrcode.main import GenericImage


class QRCode:
    """Class to generate a QR code from a given string. It uses the qrcode
    library to generate the QR code image.

    Properties:
        - `qrcode_string` (str): The QR code data string.
        - `qrcode_object` (qrcode.QRCode): The QR code object.
        - `qr_image` (GenericImage): The QR code image.

    Methods:
        - `qrcode_cli_show`: Show the QR code in the terminal.
        - `qrcode_cv_window_show`: Show the QR code in a window, using the
            OpenCV library.

    Args:
        qrcode_data (str): The QR code data string.
        fill_color (str, optional): The fill color of the QR code. Defaults to
            'black'.
        back_color (str, optional): The background color of the QR code.
            Defaults to 'white'.
    """

    def __init__(
        self,
        qrcode_data: str,
        fill_color: str = 'black',
        back_color: str = 'white',
    ) -> None:
        self.__qrcode_data = qrcode_data
        self.__object = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=2,
        )
        self.__object.add_data(self.__qrcode_data)
        self.__qr_image = self.__object.make_image(
            fill_color=fill_color,
            back_color=back_color,
        )

    @property
    def qrcode_string(self) -> str:
        """Returns the QR code data string.

        Returns:
            str: The QR code data string.
        """
        return self.__qrcode_data

    @qrcode_string.setter
    def qrcode_string(self, value: str) -> None:
        """Sets the QR code data string.

        Args:
            value (str): The QR code data string.
        """
        if not isinstance(value, str):
            raise TypeError('The QR code data must be a string.')
        self.__qrcode_data = value

    @property
    def qrcode_object(self) -> qrcode.QRCode:
        """Returns the QR code object.

        Returns:
            qrcode.QRCode: The QR code object.
        """
        return self.__object

    @property
    def qr_image(self) -> GenericImage:
        """Returns the QR code image.

        Returns:
            GenericImage: The QR code image.
        """
        return self.__qr_image

    def qrcode_cli_show(self) -> None:
        """Show the QR code in the terminal."""
        self.__object.print_ascii(tty=True)

    def __get_img_cv(
        self,
        size: int = 400,
    ) -> cv.typing.MatLike:
        """Get the QR code image in OpenCV format.

        Args:
            size (int, optional): The size of the image. Defaults to 400.
                Applies to both width and height.

        Returns:
            cv.typing.MatLike: The QR code image in OpenCV format.
        """
        img_rgb = self.__qr_image.convert('RGB')
        img_mat = cv.cvtColor(np.array(img_rgb), cv.COLOR_RGB2BGR)

        return cv.resize(img_mat, (size, size))

    def qrcode_cv_window_show(
        self,
        delay: int = 0,
        size: int = 400,
    ) -> None:
        """Show the QRCode in a window, using the OpenCV library.
        It expects the user to close the window to continue the execution
        of the program.

        Args:
            delay (int, optional): The delay in milliseconds to show the
                window. Defaults to 0. If it is 0, the window will be shown
                until the user closes
            size (int, optional): The size of the image. Defaults to 400.
                Applies to both width and height.
        """
        cv.imshow('QRCode', self.__get_img_cv(size=size))
        cv.waitKey(delay=delay)
        cv.destroyAllWindows()
