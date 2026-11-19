import subprocess

from pytest_mock import MockerFixture

from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.usb_device_scanner import UsbDeviceScanner


ADB_DEVICES_SAMPLE = (
    'List of devices attached\n'
    'emulator-5554\tdevice\n'
    'R58M12345AB\tdevice\n'
    'UNAUTH-01\tunauthorized\n'
    '192.168.1.10:5555\tdevice\n'
)


def test_list_all_devices_includes_hyphens_and_excludes_wifi(
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        'device_manager.connection.utils.usb_device_scanner.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=['adb', 'devices'],
            returncode=0,
            stdout=ADB_DEVICES_SAMPLE,
        ),
    )
    scanner = UsbDeviceScanner(subprocess_check_flag=False)
    devices = scanner.list_all_devices()
    assert devices == {
        'emulator-5554': 'device',
        'R58M12345AB': 'device',
        'UNAUTH-01': 'unauthorized',
    }


def test_list_connected_devices_returns_usb_service_infos(
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        'device_manager.connection.utils.usb_device_scanner.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=['adb', 'devices'],
            returncode=0,
            stdout=ADB_DEVICES_SAMPLE,
        ),
    )
    scanner = UsbDeviceScanner(subprocess_check_flag=False)
    devices = scanner.list_connected_devices()
    serials = [d.serial_number for d in devices]
    assert serials == ['emulator-5554', 'R58M12345AB']
    assert all(d.connection == ConnectionType.USB for d in devices)


def test_validate_connection_with_and_without_output(mocker: MockerFixture) -> None:
    mocker.patch(
        'device_manager.connection.utils.usb_device_scanner.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=['adb', 'devices'],
            returncode=0,
            stdout=ADB_DEVICES_SAMPLE,
        ),
    )
    scanner = UsbDeviceScanner(subprocess_check_flag=False)
    assert scanner.validate_connection('emulator-5554') is True
    assert scanner.validate_connection('UNAUTH-01', devices_connected=ADB_DEVICES_SAMPLE) is False


def test_check_authorization(mocker: MockerFixture) -> None:
    mocker.patch(
        'device_manager.connection.utils.usb_device_scanner.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=['adb', 'devices'],
            returncode=0,
            stdout=ADB_DEVICES_SAMPLE,
        ),
    )
    scanner = UsbDeviceScanner(subprocess_check_flag=False)
    assert scanner.check_authorization('emulator-5554') is True
    assert scanner.check_authorization('UNAUTH-01') is False
    assert scanner.check_authorization('MISSING') is False
