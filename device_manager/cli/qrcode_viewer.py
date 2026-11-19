import io
from typing import Any
import cv2 as cv
import numpy as np

from qrcode.image.base import BaseImage


def show_qr_cli(qrcode_object: Any) -> None:
    """Render the QR code in the terminal."""
    qrcode_object.print_ascii(tty=True)


def show_qr_window(
    qr_image: BaseImage,
    delay: int = 0,
    size: int = 400,
) -> None:
    """Display the QR code image in an OpenCV GUI window."""
    image_buffer = io.BytesIO()
    qr_image.save(image_buffer)
    img_mat = cv.imdecode(
        np.frombuffer(image_buffer.getvalue(), dtype=np.uint8),
        cv.IMREAD_COLOR,
    )
    resized = cv.resize(img_mat, (size, size))
    cv.imshow('QRCode', resized)
    cv.waitKey(delay=delay)
    cv.destroyAllWindows()
