import pytest
from pytest_mock import MockerFixture

from device_manager.cli.qrcode_viewer import show_qr_cli, show_qr_window
from device_manager.utils.qrcode import QRCode


def test_qrcode_string_setter_rebuilds_image() -> None:
    qr = QRCode('initial-data')
    first_object = qr.qrcode_object
    first_image = qr.qr_image

    assert qr.qrcode_string == 'initial-data'

    qr.qrcode_string = 'updated-data'
    assert qr.qrcode_string == 'updated-data'
    assert qr.qrcode_object is not first_object
    assert qr.qr_image is not first_image


def test_qrcode_string_setter_rejects_non_string() -> None:
    qr = QRCode('data')
    with pytest.raises(TypeError, match='must be a string'):
        qr.qrcode_string = 12345


def test_qrcode_viewer_cli_and_cv_window(mocker: MockerFixture) -> None:
    qr = QRCode('data')
    mock_print = mocker.patch.object(qr.qrcode_object, 'print_ascii')
    show_qr_cli(qr.qrcode_object)
    mock_print.assert_called_once_with(tty=True)

    mock_imshow = mocker.patch('cv2.imshow')
    mock_wait = mocker.patch('cv2.waitKey')
    mock_destroy = mocker.patch('cv2.destroyAllWindows')

    show_qr_window(qr.qr_image, delay=10, size=200)
    mock_imshow.assert_called_once()
    mock_wait.assert_called_once_with(delay=10)
    mock_destroy.assert_called_once()
