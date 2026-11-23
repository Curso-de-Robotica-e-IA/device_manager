"""Unit tests covering all 6 GitHub Project board issues (100% coverage)."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.adb_executor import execute_adb_command
from device_manager.connection.device_connection import DeviceConnection
from device_manager.connection.strategies import WifiConnectionStrategy
from device_manager.connection.utils.connection_status import (
    ConnectionInfoStatus,
)
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.exceptions.errors import DeviceDisconnectedError
from device_manager.utils.adb_parsers import find_text_bounds_center


# ============================================================================
# Issue #1: Targeted Wi-Fi reconnect before full ADB server kill-server
# ============================================================================
def test_wifi_strategy_targeted_reconnect_avoids_kill_server() -> None:
    connector = MagicMock()
    connector.connection.check_wireless_adb_service_for.return_value = (
        ConnectionInfoStatus.CHANGED
    )
    connector.connection.check_devices_adb_connection.return_value = False
    connector.validate_connection.return_value = True
    svc = ServiceInfo('WIFI-1', '10.0.0.1', 5555, ConnectionType.WIFI)

    assert (
        WifiConnectionStrategy().validate(
            connector, svc, force_reconnect=True
        )
        is True
    )
    connector.establish_first_connection.assert_called_once_with('WIFI-1')
    connector.disconnect.assert_not_called()
    connector.connect_all_devices.assert_not_called()


def test_wifi_strategy_falls_back_to_full_reconnect_when_targeted_fails() -> None:
    connector = MagicMock()
    connector.connection.check_wireless_adb_service_for.return_value = (
        ConnectionInfoStatus.CHANGED
    )
    connector.connection.check_devices_adb_connection.return_value = False
    connector.validate_connection.side_effect = [False, True]
    svc = ServiceInfo('WIFI-2', '10.0.0.2', 5555, ConnectionType.WIFI)

    assert (
        WifiConnectionStrategy().validate(
            connector, svc, force_reconnect=True
        )
        is True
    )
    connector.disconnect.assert_called_once_with()
    connector.connect_all_devices.assert_called_once_with()


# ============================================================================
# Issue #2: validate_connection raises DeviceDisconnectedError when requested
# ============================================================================
def test_validate_connection_raise_on_error(mocker: MockerFixture) -> None:
    gw = MagicMock()
    dc = DeviceConnection(gateway=gw)

    with pytest.raises(
        DeviceDisconnectedError, match='No devices currently connected'
    ):
        dc.validate_connection('MISSING', raise_on_error=True)

    dc.connection_info['USB-1'] = ServiceInfo(
        'USB-1', '', 0, ConnectionType.USB
    )
    mocker.patch.object(
        dc.usb_scanner, 'validate_connection', return_value=False
    )
    with pytest.raises(
        DeviceDisconnectedError, match='Failed to validate connection'
    ):
        dc.validate_connection('USB-1', raise_on_error=True)


# ============================================================================
# Issue #3: subprocess_check_flag returns returncode & stderr in CalledProcessError
# ============================================================================
def test_execute_adb_command_check_flag_preserves_returncode_and_stderr() -> None:
    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=['adb', '-s', 'SER1', 'shell', 'bad'],
        returncode=127,
        stdout='partial',
        stderr='bad: not found',
    )

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        execute_adb_command(
            'bad',
            ['SER1'],
            shell=True,
            subprocess_check_flag=True,
            capture_output=False,
            gateway=gw,
        )

    assert exc_info.value.returncode == 127
    assert exc_info.value.stderr == 'bad: not found'
    assert exc_info.value.output == 'partial'


# ============================================================================
# Issue #4: unlock_screen with swipe fallback
# ============================================================================
def test_unlock_screen_fallback_swipe_and_no_fallback(
    mocker: MockerFixture,
) -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    actions = DeviceActions(conn, 'SER1')
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )

    # fallback_swipe=False -> only KEYCODE_MENU
    actions.unlock_screen(fallback_swipe=False)
    assert mock_exec.call_count == 1

    # fallback_swipe=True and still locked -> dismiss-keyguard + swipe
    mock_exec.reset_mock()
    mock_exec.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout=''),
        subprocess.CompletedProcess(
            args=[], returncode=0, stdout='  mScreenLocked=true\n'
        ),
        subprocess.CompletedProcess(args=[], returncode=0, stdout=''),
        subprocess.CompletedProcess(args=[], returncode=0, stdout=''),
    ]
    actions.unlock_screen(fallback_swipe=True)
    assert mock_exec.call_count == 4

    # fallback_swipe=True and dumpsys has no mScreenLocked -> no swipe
    mock_exec.reset_mock()
    mock_exec.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout=''),
        subprocess.CompletedProcess(args=[], returncode=0, stdout='no flag'),
    ]
    actions.unlock_screen(fallback_swipe=True)
    assert mock_exec.call_count == 2


# ============================================================================
# Issue #5: click_by_text + find_text_bounds_center
# ============================================================================
def test_find_text_bounds_center_and_click_by_text(
    mocker: MockerFixture,
) -> None:
    sample_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<hierarchy>'
        '  <node text="" content-desc="Settings" bounds="[100,200][300,400]" />'
        '  <node text="Continue" content-desc="" bounds="[0,0][200,100]" />'
        '  <node text="NoBounds" content-desc="" bounds="invalid" />'
        '</hierarchy>'
    )
    assert find_text_bounds_center('', 'Continue') is None
    assert find_text_bounds_center('<broken', 'Continue') is None
    assert find_text_bounds_center(sample_xml, 'continue') == (100, 50)
    assert find_text_bounds_center(sample_xml, 'Continue', exact=True) == (
        100,
        50,
    )
    assert find_text_bounds_center(sample_xml, 'settings') == (200, 300)
    assert find_text_bounds_center(sample_xml, 'NoBounds') is None
    assert find_text_bounds_center(sample_xml, 'Missing') is None

    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    actions = DeviceActions(conn, 'SER1')
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command',
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=f'UI hierchary dumped to: /dev/tty\n{sample_xml}',
        ),
    )
    assert actions.click_by_text('Continue') is True
    assert actions.click_by_text('NotPresent', xml_content=sample_xml) is False
    assert mock_exec.call_count == 2  # dump + tap


# ============================================================================
# Issue #6: Native ADB uiautomator dump XML (without uiautomator2)
# ============================================================================
def test_device_info_native_get_screen_gui_xml(
    mocker: MockerFixture,
) -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = False
    info = DeviceInfo(conn, 'SER1')
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )

    # 1. Direct /dev/tty XML
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='UI dumped\n<?xml version="1.0"?><hierarchy/>',
    )
    assert info.get_screen_gui_xml() == '<?xml version="1.0"?><hierarchy/>'

    # 2. Fallback to /sdcard/window_dump.xml when /dev/tty has no <?xml
    mock_exec.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout='no xml'),
        subprocess.CompletedProcess(
            args=[], returncode=0, stdout='<?xml version="1.0"?><fb/>'
        ),
    ]
    assert info.get_screen_gui_xml() == '<?xml version="1.0"?><fb/>'

    # 3. Disconnected on first or fallback query -> None
    mock_exec.side_effect = None
    mock_exec.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=''
    )
    assert info.get_screen_gui_xml() is None
    assert info.get_screen_gui_xml(use_uiautomator2=True) is None

    mock_exec.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout='no xml'),
        subprocess.CompletedProcess(args=[], returncode=1, stdout=''),
    ]
    assert info.get_screen_gui_xml() is None
