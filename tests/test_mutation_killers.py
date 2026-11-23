"""Targeted mutation-killing unit tests (Given-When-Then) for Wave 1 modules."""

from __future__ import annotations

import logging
import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.adb_executor import execute_adb_command
from device_manager.components.object_manager import ObjectManager
from device_manager.connection.strategies import (
    UsbConnectionStrategy,
    WifiConnectionStrategy,
)
from device_manager.connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.utils.adb_parsers import parse_getprop
from device_manager.utils.dm_warnings import check_adb_dependencies_version


# ============================================================================
# 1. ObjectManager (kills remove__mutmut_5, get__mutmut_4, get__mutmut_6)
# ============================================================================
def test_object_manager_remove_absent_and_get_custom_default() -> None:
    mgr: ObjectManager[str] = ObjectManager()
    mgr.add('present', 'value')

    # Removing a missing key must be a safe no-op (not raise KeyError)
    mgr.remove('absent')
    assert 'present' in mgr

    # Custom default must be returned verbatim when key is missing
    assert mgr.get('absent', default='custom-fallback') == 'custom-fallback'


# ============================================================================
# 2. adb_parsers (kills parse_getprop__mutmut_8/9/11/31/32/35/36)
# ============================================================================
def test_parse_getprop_preserves_colons_in_values_and_all_base_keys() -> None:
    raw = (
        '[ro.serialno]: [SER-01]\n'
        '[ro.product.manufacturer]: [Google]\n'
        '[ro.product.model]: [Pixel: Pro: Max]\n'
        '[ro.build.version.release]: [14]\n'
        '[custom.prop]: [a: b: c]\n'
    )
    result = parse_getprop(raw, extra_keys=['custom.prop'])
    assert result == {
        'serial_number': 'SER-01',
        'brand': 'Google',
        'model': 'Pixel: Pro: Max',
        'android_version': '14',
        'custom.prop': 'a: b: c',
    }


# ============================================================================
# 3. adb_executor (kills default args, gateway=None fallback, duration & logs)
# ============================================================================
def test_execute_adb_command_defaults_and_fallback_gateway(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Exact error message for empty comm_uris
    with pytest.raises(
        ValueError,
        match=r'^No devices specified for command execution\.$',
    ):
        execute_adb_command('get-state', [])

    # Default gateway=None must delegate to subprocess.run with shell=False, check=False
    mock_run = mocker.patch(
        'device_manager.adb_executor.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=['adb', '-s', 'SER1', 'get-state'],
            returncode=0,
            stdout='device\n',
        ),
    )
    mocker.patch(
        'device_manager.adb_executor.perf_counter',
        side_effect=[10.0, 10.25],
    )
    with caplog.at_level(logging.DEBUG, logger='device_manager.adb_executor'):
        execute_adb_command('get-state', ['SER1'])

    mock_run.assert_called_once_with(
        ['adb', '-s', 'SER1', 'get-state'],
        shell=False,
        check=False,
        capture_output=False,
        text=None,
    )
    assert any(
        r.message
        == 'ADB command succeeded: uri=SER1 command=get-state returncode=0 duration_ms=250.0'
        for r in caplog.records
    )


def test_execute_adb_command_failure_log_exact_format(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=['adb', '-s', 'SER1', 'bad'],
        returncode=1,
        stdout='',
        stderr='  boom  ',
    )
    mocker.patch(
        'device_manager.adb_executor.perf_counter',
        side_effect=[2.0, 2.5],
    )
    with caplog.at_level(logging.WARNING, logger='device_manager.adb_executor'):
        execute_adb_command('bad', ['SER1'], capture_output=True, gateway=gw)

    assert any(
        r.message
        == 'ADB command failed: uri=SER1 command=bad returncode=1 duration_ms=500.0 stderr=boom'
        for r in caplog.records
    )


# ============================================================================
# 4. Connection Strategies (kills Usb/Wifi validate argument, `or`->`and`, logs)
# ============================================================================
def test_usb_strategy_validate_passes_exact_serial() -> None:
    connector = MagicMock()
    connector.usb_scanner.validate_connection.return_value = True
    svc = ServiceInfo('USB-99', '', 0, ConnectionType.USB)

    assert UsbConnectionStrategy().validate(connector, svc) is True
    connector.usb_scanner.validate_connection.assert_called_once_with('USB-99')


@pytest.mark.parametrize(
    ('mdns_status', 'adb_connected'),
    [
        pytest.param(
            ConnectionInfoStatus.UPDATED,
            False,
            id='updated_but_adb_disconnected',
        ),
        pytest.param(
            ConnectionInfoStatus.CHANGED,
            True,
            id='changed_but_adb_connected',
        ),
    ],
)
def test_wifi_strategy_validate_single_fault_no_reconnect(
    mdns_status: ConnectionInfoStatus,
    adb_connected: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    connector = MagicMock()
    connector.connection.check_wireless_adb_service_for.return_value = (
        mdns_status
    )
    connector.connection.check_devices_adb_connection.return_value = (
        adb_connected
    )
    svc = ServiceInfo('WIFI-1', '10.0.0.1', 5555, ConnectionType.WIFI)

    with caplog.at_level(
        logging.DEBUG, logger='device_manager.connection.strategies'
    ):
        result = WifiConnectionStrategy().validate(connector, svc)

    assert result is False
    connector.connection.check_wireless_adb_service_for.assert_called_once_with(
        svc
    )
    connector.connection.check_devices_adb_connection.assert_called_once_with(
        '10.0.0.1:5555'
    )
    connector.establish_first_connection.assert_not_called()
    expected_msg = (
        'Wi-Fi validation failed (no reconnect): '
        f'serial=WIFI-1 uri=10.0.0.1:5555 mdns_status={mdns_status.name} '
        f'adb_connected={adb_connected}'
    )
    assert any(r.message == expected_msg for r in caplog.records)


def test_wifi_strategy_validate_force_reconnect_logs_exact_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    connector = MagicMock()
    connector.connection.check_wireless_adb_service_for.return_value = (
        ConnectionInfoStatus.UPDATED
    )
    connector.connection.check_devices_adb_connection.return_value = False
    connector.validate_connection.side_effect = [False, True]
    svc = ServiceInfo('WIFI-2', '10.0.0.2', 5555, ConnectionType.WIFI)

    with caplog.at_level(
        logging.WARNING, logger='device_manager.connection.strategies'
    ):
        result = WifiConnectionStrategy().validate(
            connector, svc, force_reconnect=True
        )

    assert result is True
    connector.establish_first_connection.assert_called_once_with('WIFI-2')
    connector.disconnect.assert_called_once_with()
    connector.connect_all_devices.assert_called_once_with()
    assert connector.validate_connection.call_count == 2
    expected_msg = (
        'Wi-Fi connection invalid; attempting targeted reconnect: '
        'serial=WIFI-2 uri=10.0.0.2:5555 mdns_status=UPDATED adb_connected=False'
    )
    assert any(r.message == expected_msg for r in caplog.records)


# ============================================================================
# 5. dm_warnings (kills subprocess args, case-insensitive split, warning logs)
# ============================================================================
def test_check_adb_dependencies_version_exact_subprocess_and_warning_log(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    mock_run = mocker.patch(
        'device_manager.utils.dm_warnings.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=['adb', 'version'],
            returncode=0,
            stdout=(
                'Android Debug Bridge VERSION 2.1.41\n'
                'VERSION 36.1.2-10900879\n'
            ),
        ),
    )

    with caplog.at_level(
        logging.DEBUG, logger='device_manager.utils.dm_warnings'
    ):
        check_adb_dependencies_version()

    mock_run.assert_called_once_with(
        args=['adb', 'version'],
        capture_output=True,
        check=True,
        text=True,
    )
    assert any(
        r.message
        == 'Your current major adb version might not work as intended. Recommended: 1.0.41'
        for r in caplog.records
    )
    assert any(
        r.message
        == 'Your current minor Android SDK version might not work as intended. Recommended: 35.0.2'
        for r in caplog.records
    )
    assert any(
        r.message == 'ADB dependencies verified (adb=2.1.41, sdk=36.1.2-10900879)'
        for r in caplog.records
    )
