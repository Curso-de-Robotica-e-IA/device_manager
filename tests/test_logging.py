import logging
import subprocess
from unittest.mock import MagicMock

import pytest

import device_manager
from device_manager.adb_executor import execute_adb_command
from device_manager.connection.adb_pairing import AdbPairing
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.manager import DeviceManager


def test_root_logger_has_null_handler() -> None:
    root_pkg_logger = logging.getLogger(device_manager.__name__)
    assert any(isinstance(h, logging.NullHandler) for h in root_pkg_logger.handlers)


def test_execute_adb_command_logs_debug_and_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    class FakeGateway:
        def __init__(self, rc: int, stderr: str = '') -> None:
            self.rc = rc
            self.stderr = stderr

        def run(self, args, *, check=False, capture_output=False, text=None):
            return subprocess.CompletedProcess(
                args=list(args),
                returncode=self.rc,
                stdout='',
                stderr=self.stderr,
            )

    with caplog.at_level(logging.DEBUG, logger='device_manager.adb_executor'):
        execute_adb_command(
            command='shell ls',
            comm_uris=['emulator-5554'],
            gateway=FakeGateway(rc=0),
        )
        execute_adb_command(
            command='shell badcmd',
            comm_uris=['emulator-5554'],
            capture_output=True,
            gateway=FakeGateway(rc=1, stderr='not found'),
        )

    assert any(
        r.levelno == logging.DEBUG and 'ADB command succeeded' in r.message
        for r in caplog.records
    )
    assert any(
        r.levelno == logging.WARNING
        and 'ADB command failed' in r.message
        and 'not found' in r.message
        for r in caplog.records
    )


def test_adb_pairing_logs_outcome_without_leaking_password(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret_password = 'SUPER_SECRET_PAIR_PASS'

    class FakeGateway:
        def run(self, args, *, check=False, capture_output=False, text=None):
            return subprocess.CompletedProcess(
                args=list(args),
                returncode=0,
                stdout='Successfully paired to 192.168.1.50:40000\n',
            )

    pairing = AdbPairing(password=secret_password, gateway=FakeGateway())
    pairing._context.add_service(
        'dev1',
        ServiceInfo('dev1', '192.168.1.50', 40000, ConnectionType.WIFI),
    )

    with caplog.at_level(logging.INFO, logger='device_manager.connection.adb_pairing'):
        assert pairing.pair_devices() is True

    assert 'Successfully paired device: uri=192.168.1.50:40000' in caplog.text
    assert secret_password not in caplog.text


def test_device_manager_connect_devices_logs_missing_and_connected(
    caplog: pytest.LogCaptureFixture,
) -> None:
    usb_service = ServiceInfo('USB1', '', 0, ConnectionType.USB)
    conn = MagicMock()
    conn.usb_scanner.list_connected_devices.return_value = []
    conn.visible_devices.return_value = [usb_service]
    conn.is_connected.return_value = True
    conn.build_comm_uri.return_value = 'USB1'

    dm = DeviceManager(check_dependencies=False, connector=conn)
    with caplog.at_level(logging.INFO, logger='device_manager.manager'):
        dm.connect_devices('USB1', 'MISSING')

    assert 'Requested device not visible for connection: serial=MISSING' in caplog.text
    assert "Connected devices: requested=2 connected=['USB1']" in caplog.text
