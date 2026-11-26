"""Weak Robust Equivalence Class tests closing all remaining branches across
CameraActions, DeviceManager, DeviceInfo, DeviceActions, BaseDeviceComponent,
DevicePromptCLI, AppInfo, adb_executor, and adb_parsers.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.actions.camera_actions import CameraActions
from device_manager.adb_executor import execute_adb_command
from device_manager.base_device_component import (
    BaseDeviceComponent,
    require_connection,
)
from device_manager.cli.device_prompt import DevicePromptCLI
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.device_actions import DeviceActions
from device_manager.device_info import DeviceInfo
from device_manager.exceptions.errors import (
    DeviceDisconnectedError,
    UnexpectedAdbOutputError,
)
from device_manager.infos.app import AppInfo
from device_manager.manager import DeviceManager
from device_manager.utils.adb_parsers import (
    parse_app_path,
    parse_current_activity,
)


# ============================================================================
# 1. CameraActions — pull_pictures & pull_picture_by_name Weak Robust
# ============================================================================
def _make_camera(connected: bool = True) -> CameraActions:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    return CameraActions(
        device_connection=conn,
        serial_number='emulator-5554',
        subprocess_check_flag=False,
        comm_uri='emulator-5554',
        validate_connection_callback=lambda: connected,
    )


def test_camera_actions_pull_pictures_and_clear_path_valid(
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command',
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='img1.jpg\nimg2.jpg\n',
        ),
    )
    cam = _make_camera(connected=True)
    cam.clear_pictures(Path('/sdcard/DCIM/Camera/*'))

    dest_dir = tmp_path / 'new_subdir'
    cam.pull_pictures(str(dest_dir), amount=1)
    assert dest_dir.exists()
    assert mock_exec.call_count == 3


@pytest.mark.parametrize(
    ('scenario', 'expected_exc', 'match_pattern'),
    [
        pytest.param(
            'dest_is_file',
            RuntimeError,
            r'Failed to create destination directory: Destination must be a directory\.',
            id='[Idest1,Vc1]-pull_pictures_dest_is_file',
        ),
        pytest.param(
            'disconnected',
            RuntimeError,
            r'Failed to pull pictures: Device connection is not valid\.',
            id='[Vdest1,Ic1]-pull_pictures_disconnected',
        ),
        pytest.param(
            'by_name_disconnected',
            DeviceDisconnectedError,
            r'Device connection is not valid\. Cannot pull image\.',
            id='[Vname1,Ic1]-pull_by_name_disconnected',
        ),
        pytest.param(
            'by_name_zero_pulled',
            RuntimeError,
            r"Failed to pull image 'a\.jpg': File not found on device or 0 files pulled",
            id='[Iout1,Vc1]-pull_by_name_zero_files',
        ),
        pytest.param(
            'by_name_multi_pulled',
            RuntimeError,
            r"Failed to pull image 'a\.jpg': Multiple files were pulled \(2\)",
            id='[Iout2,Vc1]-pull_by_name_multiple_files',
        ),
        pytest.param(
            'by_name_adb_error',
            RuntimeError,
            r"Failed to pull image 'a\.jpg': ADB pull failed or file not found",
            id='[Iout3,Vc1]-pull_by_name_error_text',
        ),
        pytest.param(
            'mkdir_os_error',
            RuntimeError,
            r'Failed to ensure destination directory',
            id='[Idest2,Vc1]-verify_path_permission_error',
        ),
    ],
)
def test_camera_actions_weak_robust_invalid(
    scenario: str,
    expected_exc: type[Exception],
    match_pattern: str,
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    if scenario == 'dest_is_file':
        file_path = tmp_path / 'not_a_dir.txt'
        file_path.write_text('x', encoding='utf-8')
        cam = _make_camera(connected=True)
        with pytest.raises(expected_exc, match=match_pattern):
            cam.pull_pictures(file_path)
    elif scenario == 'disconnected':
        cam = _make_camera(connected=False)
        with pytest.raises(expected_exc, match=match_pattern):
            cam.pull_pictures(tmp_path)
    elif scenario == 'by_name_disconnected':
        cam = _make_camera(connected=False)
        with pytest.raises(expected_exc, match=match_pattern):
            cam.pull_picture_by_name('a.jpg', tmp_path)
    elif scenario == 'mkdir_os_error':
        cam = _make_camera(connected=True)
        mocker.patch.object(
            Path, 'mkdir', side_effect=PermissionError('denied')
        )
        with pytest.raises(expected_exc, match=match_pattern):
            cam.pull_picture_by_name('a.jpg', tmp_path)
    else:
        stdout_map = {
            'by_name_zero_pulled': '0 files pulled, 0 skipped.\n',
            'by_name_multi_pulled': '2 files pulled, 0 skipped.\n',
            'by_name_adb_error': 'adb: error: remote object does not exist\n',
        }
        mocker.patch(
            'device_manager.base_device_component.execute_adb_command',
            return_value=subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=stdout_map[scenario],
            ),
        )
        cam = _make_camera(connected=True)
        with pytest.raises(expected_exc, match=match_pattern):
            cam.pull_picture_by_name('a.jpg', tmp_path)


# ============================================================================
# 2. DeviceManager remaining paths — Weak Robust
# ============================================================================
def test_device_manager_remaining_methods_weak_robust(
    mocker: MockerFixture,
) -> None:
    mock_check = mocker.patch(
        'device_manager.manager.check_adb_dependencies_version'
    )
    usb_svc = ServiceInfo('USB1', '', 0, ConnectionType.USB)
    wifi_svc = ServiceInfo('WIFI1', '10.0.0.5', 5555, ConnectionType.WIFI)
    conn = MagicMock()
    conn.usb_scanner.list_connected_devices.return_value = [usb_svc]
    conn.connection_info.get.side_effect = [None, None]
    conn.build_comm_uri.return_value = 'USB1'
    conn.is_connected.return_value = True

    dm = DeviceManager(check_dependencies=True, connector=conn)
    dm.load_connected_usb_devices()
    mock_check.assert_called_once()
    conn.connection_info.add.assert_called_once_with('USB1', usb_svc)

    assert 'USB1' in repr(dm)
    assert 'USB1' in str(dm)
    assert dm.get_device_info('USB1') is not None
    assert dm.get_device_info('MISSING') is None
    assert dm.get_device_actions('USB1') is not None
    assert dm.get_device_actions('MISSING') is None
    assert dm.is_connected('USB1') is True

    dm.adb_pairing_instance(service_name='svc')
    assert dm.adb_pair is not None

    # execute_adb_command skips serial when service_info is None, and resolves Wi-Fi URI
    mock_exec = mocker.patch('device_manager.manager.execute_adb_command')
    dm.execute_adb_command('shell ls')
    assert mock_exec.call_args.kwargs['comm_uris'] == []

    dm._register_device('WIFI1')
    conn.connection_info.get.side_effect = None
    conn.connection_info.get.side_effect = (
        lambda s: wifi_svc if s == 'WIFI1' else None
    )
    dm.execute_adb_command('shell ls')
    assert mock_exec.call_args.kwargs['comm_uris'] == ['10.0.0.5:5555']

    # disconnect_devices failure vs success
    conn.stop_connection.return_value = False
    assert dm.disconnect_devices('USB1') is False
    assert 'USB1' in dm

    conn.stop_connection.return_value = True
    conn.connection_info.get.side_effect = None
    conn.connection_info.get.return_value = None
    assert dm.disconnect_devices('USB1') is True
    assert 'USB1' not in dm

    # __delitem__
    dm._register_device('USB1')
    del dm['USB1']
    assert 'USB1' not in dm


# ============================================================================
# 3. DeviceInfo disconnected paths + app() — Weak Robust
# ============================================================================
def test_device_info_disconnected_weak_robust_invalid() -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    conn.validate_connection.return_value = False
    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=1, stdout='', stderr='error: device not found'
    )

    info = DeviceInfo(conn, 'emulator-5554', gateway=gw)
    assert info.actual_activity() is None
    assert isinstance(info.app('com.example'), AppInfo)

    with pytest.raises(UnexpectedAdbOutputError, match='Unexpected output'):
        info.is_screen_on()
    with pytest.raises(UnexpectedAdbOutputError, match='Unexpected output'):
        info.is_device_locked()
    with pytest.raises(UnexpectedAdbOutputError, match='Unexpected output'):
        info.get_properties()
    with pytest.raises(UnexpectedAdbOutputError, match='Unexpected output'):
        info.get_screen_dimensions()


# ============================================================================
# 4. Remaining micro-branches (BaseDeviceComponent, DeviceActions,
#    DevicePromptCLI, adb_executor kwargs, AppInfo, adb_parsers)
# ============================================================================
def test_remaining_edge_branches(mocker: MockerFixture) -> None:
    # BaseDeviceComponent.validate_connection & require_connection(raise_on_disconnect=False)
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    conn.validate_connection.return_value = False

    class _SilentComponent(BaseDeviceComponent):
        @require_connection(raise_on_disconnect=False)
        def do_work(self) -> str:
            return 'done'

    comp = _SilentComponent(conn, 'emulator-5554')
    assert comp.do_work() is None

    # DeviceActions.safe_screencap_bytes returning None on empty stdout
    conn.validate_connection.return_value = True
    mocker.patch(
        'device_manager.device_actions.subprocess.run',
        return_value=subprocess.CompletedProcess(
            args=[], returncode=1, stdout=b''
        ),
    )
    actions = DeviceActions(conn, 'emulator-5554')
    assert actions.safe_screencap_bytes() is None

    # adb_executor with kwargs
    class _KwGateway:
        def __init__(self) -> None:
            self.last_args: list[str] = []

        def run(self, args, *, check=False, capture_output=False, text=None):
            self.last_args = list(args)
            return subprocess.CompletedProcess(
                args=list(args), returncode=0, stdout=''
            )

    gw = _KwGateway()
    execute_adb_command(
        'ls', ['emulator-5554'], gateway=gw, **{'-l': '/sdcard'}
    )
    assert gw.last_args[-2:] == ['-l', '/sdcard']

    # DevicePromptCLI failure branch and refresh ('0') branch
    cm = MagicMock()
    cm.device_pairing.return_value = False
    cm.available_devices.return_value = {
        'D1': ServiceInfo('D1', '10.0.0.1', 5555, ConnectionType.WIFI),
    }
    mocker.patch(
        'device_manager.cli.device_prompt.Prompt.ask',
        side_effect=['N', '0', '1', 'N'],
    )
    cli = DevicePromptCLI(cm, console=MagicMock())
    cli.check_pairing()
    assert cli.select_devices_to_connect() == ['D1']
    assert cm.available_devices.call_count == 2

    # AppInfo.get_action fallback branch (no line ends with action)
    conn.validate_connection.return_value = False
    app = AppInfo('com.example', conn, 'emulator-5554')
    app.dumpsys = '  Action: "android.intent.action.MAIN_TEST"\n'
    assert 'MAIN_TEST' in app.get_action('MAIN')

    # adb_parsers edge branches
    assert (
        parse_current_activity('  mCurrentFocus=Window{no_pkg_here}\n')
        == 'No activity'
    )
    assert parse_app_path('no package line here\n') is None


# ============================================================================
# 5. Weak Robust Branch Completion (100% Statement & Branch Coverage)
# ============================================================================
def test_weak_robust_remaining_branches_sync(
    tmp_path,
    mocker: MockerFixture,
) -> None:
    from device_manager.actions.camera_actions import CameraActions
    from device_manager.components.object_manager import ObjectManager
    from device_manager.connection.device_connection import DeviceConnection
    from device_manager.connection.utils.mdns_context import MDnsContext
    from device_manager.connection.utils.mdns_listener import MDnsListener
    from device_manager.connection.utils.usb_device_scanner import (
        UsbDeviceScanner,
    )
    from device_manager.utils.adb_parsers import parse_getprop

    # 1. CameraActions._validate_pull_output (neutral output -> neither match nor error)
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    conn.validate_connection.return_value = True
    cam = CameraActions(conn, 'emulator-5554', False, 'emulator-5554')
    cam._validate_adb_pull_output('done without summary', 'img.jpg')

    # 2. DevicePromptCLI: paired='Y' (skip pairing) & select multiple ('Y' then 'N')
    cm = MagicMock()
    cm.available_devices.return_value = {
        'D1': ServiceInfo('D1', '10.0.0.1', 5555, ConnectionType.WIFI),
        'D2': ServiceInfo('D2', '10.0.0.2', 5555, ConnectionType.WIFI),
    }
    mocker.patch(
        'device_manager.cli.device_prompt.Prompt.ask',
        side_effect=['Y', '1', 'Y', '2', 'N'],
    )
    cli = DevicePromptCLI(cm, console=MagicMock())
    cli.check_pairing()
    cm.device_pairing.assert_not_called()
    assert cli.select_devices_to_connect() == ['D1', 'D2']

    # 3. ObjectManager.edit on absent key (no-op)
    mgr: ObjectManager[int] = ObjectManager()
    mgr.edit('absent', 42)
    assert 'absent' not in mgr

    # 4. DeviceConnection partial branches:
    #    - is_connected returns False when device is known but absent from adb output
    #    - connect_all skips disconnected serial
    #    - __fix_adb_port no-op when validate_connection is False
    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='List of devices attached\n'
    )
    dc = DeviceConnection(gateway=gw)
    dc.connection_info['S1'] = ServiceInfo(
        'S1', '10.0.0.1', 5555, ConnectionType.WIFI
    )
    assert (
        dc.is_connected('S1', devices_connected='List of devices attached\n')
        is False
    )
    mocker.patch.object(dc, 'establish_first_connection')
    mocker.patch.object(dc, 'disconnect')
    mocker.patch.object(dc, 'connect_all_devices')
    mocker.patch.object(dc, 'is_connected', return_value=False)
    assert dc.start_connection(['S1']) == []
    mocker.patch.object(dc, 'validate_connection', return_value=False)
    dc._DeviceConnection__fix_adb_port('S1')

    # 5. MDnsListener: update/remove/add with get_service_info -> None (no-op)
    ctx = MDnsContext()
    listener = MDnsListener(ctx)
    zc = MagicMock()
    zc.get_service_info.return_value = None
    listener.update_service(zc, '_adb._tcp.local.', 'svc')
    listener.remove_service(zc, '_adb._tcp.local.', 'svc')
    listener.add_service(zc, '_adb._tcp.local.', 'svc')
    assert ctx.get_online_service() == {}

    # 6. UsbDeviceScanner: blank line, malformed line without tab, offline status
    scanner_gw = MagicMock()
    scanner_gw.run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout=(
            'List of devices attached\n'
            '\n'
            'malformed_line_without_tab\n'
            'SER-OFF\toffline\n'
        ),
    )
    scanner = UsbDeviceScanner(subprocess_check_flag=False, gateway=scanner_gw)
    assert scanner.list_all_devices() == {'SER-OFF': 'offline'}
    assert scanner.check_authorization('SER-OFF') is False

    # 7. DeviceActions.install_apk when file exists but validate_connection is False
    apk_file = tmp_path / 'sample.apk'
    apk_file.write_bytes(b'apk')
    conn.validate_connection.return_value = False
    actions = DeviceActions(conn, 'emulator-5554')
    actions.install_apk(str(apk_file))

    # 8. DeviceInfo.get_screen_gui_xml when ui_backend returns None -> None
    empty_ui = MagicMock()
    empty_ui.dump_xml.return_value = None
    info = DeviceInfo(conn, 'emulator-5554', ui_backend=empty_ui)
    assert info.get_screen_gui_xml() is None

    # 9. DeviceManager._register_device (already registered) & disconnect_devices (still in connection_info)
    mocker.patch('device_manager.manager.check_adb_dependencies_version')
    dm_conn = MagicMock()
    dm_conn.stop_connection.return_value = True
    dm_conn.connection_info = {
        'S1': ServiceInfo('S1', '10.0.0.1', 5555, ConnectionType.WIFI)
    }
    dm = DeviceManager(connector=dm_conn)
    dm._register_device('S1')
    dm._register_device('S1')  # second call hits already-registered branch
    assert dm.disconnect_devices('S1') is True
    assert 'S1' in dm

    # 10. parse_getprop: malformed line, extra_keys=None, and extra_keys with missing key
    raw_props = (
        'malformed_line\n'
        '[ro.serialno]: [SER1]\n'
        '[ro.product.manufacturer]: [Google]\n'
        '[ro.product.model]: [Pixel]\n'
        '[ro.build.version.release]: [14]\n'
    )
    assert parse_getprop(raw_props, extra_keys=None)['serial_number'] == 'SER1'
    assert 'missing.key' not in parse_getprop(
        raw_props, extra_keys=['missing.key']
    )


def test_weak_robust_remaining_branches_async() -> None:
    import asyncio

    from device_manager.asyncio_dm.async_adb_pairing import AsyncAdbPairing
    from device_manager.asyncio_dm.async_mdns_listener import AsyncMDnsListener
    from device_manager.connection.utils.mdns_context import MDnsContext

    # 1. AsyncAdbPairing._new_zeroconf_instance when zombies exceed max_zc_instances
    pairing = AsyncAdbPairing(password='123456')
    pairing._zeroconf_zombies = [MagicMock()] * (pairing._max_zc_instances + 1)
    pairing._zeroconf = None
    pairing._new_zeroconf_instance()
    assert pairing._zeroconf is None

    # 2. AsyncMDnsListener: update/remove/add when async_get_service_info returns None
    ctx = MDnsContext()
    listener = AsyncMDnsListener(ctx)

    class _NoneAsyncZc:
        async def async_get_service_info(self, type_: str, name: str):
            return None

    async def _run() -> None:
        zc = _NoneAsyncZc()
        await listener.update_service(zc, '_adb._tcp.local.', 'svc')  # type: ignore[arg-type]
        await listener.remove_service(zc, '_adb._tcp.local.', 'svc')  # type: ignore[arg-type]
        await listener.add_service(zc, '_adb._tcp.local.', 'svc')  # type: ignore[arg-type]

    asyncio.run(_run())
    assert ctx.get_online_service() == {}


def test_device_manager_defaults_forwarding_and_logs(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    from device_manager.connection.device_connection import DEFAULT_FIXED_PORT

    mock_check = mocker.patch(
        'device_manager.manager.check_adb_dependencies_version'
    )
    mock_dc_cls = mocker.patch('device_manager.manager.DeviceConnection')
    mock_dc_inst = mock_dc_cls.return_value
    usb_svc = ServiceInfo('USB-1', '', 0, ConnectionType.USB)
    mock_dc_inst.usb_scanner.list_connected_devices.return_value = [usb_svc]
    mock_dc_inst.connection_info.get.return_value = None

    with caplog.at_level(logging.INFO, logger='device_manager.manager'):
        dm = DeviceManager()
        dm.load_connected_usb_devices()

    mock_check.assert_called_once_with()
    mock_dc_cls.assert_called_once_with(
        subprocess_check_flag=False,
        fixed_port=DEFAULT_FIXED_PORT,
    )
    assert dm.adb_pair is None
    assert dm.subprocess_check is False
    assert dm._devices_fixed_port == DEFAULT_FIXED_PORT
    mock_dc_inst.connection_info.add.assert_called_once_with('USB-1', usb_svc)
    assert any(
        r.message == "Loaded connected USB devices: serials=['USB-1']"
        for r in caplog.records
    )

    mock_ap_cls = mocker.patch('device_manager.manager.AdbPairing')
    dm.adb_pairing_instance()
    mock_ap_cls.assert_called_once_with(
        service_name='robot_celular',
        service_regex_filter=None,
        subprocess_check_flag=False,
    )

    mock_exec = mocker.patch('device_manager.manager.execute_adb_command')
    mock_dc_inst.connection_info.get.return_value = usb_svc
    dm.execute_adb_command('ls')
    mock_exec.assert_called_once_with(
        command='ls',
        comm_uris=['USB-1'],
        shell=True,
        subprocess_check_flag=False,
        capture_output=False,
        gateway=mock_dc_inst._gateway,
    )
    with pytest.raises(
        TypeError,
        match=r"comm_uris must be a list, tuple or None, got <class 'int'>",
    ):
        dm.execute_adb_command('ls', comm_uris=123)  # type: ignore[arg-type]

    mock_dc_inst.stop_connection.return_value = True
    mock_dc_inst.connection_info.get.return_value = None
    with caplog.at_level(logging.INFO, logger='device_manager.manager'):
        assert dm.disconnect_devices('USB-1') is True
    assert any(
        r.message == "Disconnected devices: serials=['USB-1']"
        for r in caplog.records
    )

    mock_dc_inst.stop_connection.return_value = False
    with caplog.at_level(logging.WARNING, logger='device_manager.manager'):
        assert dm.disconnect_devices('USB-1') is False
    assert any(
        r.message
        == "Failed to disconnect all requested devices: serials=['USB-1']"
        for r in caplog.records
    )


def test_base_device_component_and_require_connection_exact_defaults(
    mocker,
) -> None:
    from unittest.mock import MagicMock

    import pytest

    from device_manager.base_device_component import (
        BaseDeviceComponent,
        require_connection,
    )
    from device_manager.exceptions.errors import DeviceDisconnectedError

    class _Dummy(BaseDeviceComponent):
        @require_connection(raise_on_disconnect=True)
        def op(self) -> str:
            return 'ok'

    conn = MagicMock()
    conn.validate_connection.return_value = False
    conn.build_comm_uri.return_value = '10.0.0.1:5555'

    comp = _Dummy(conn, 'S1')
    assert comp.subprocess_check_flag is False
    with pytest.raises(
        DeviceDisconnectedError, match='^Device connection is not valid\\.$'
    ):
        comp.op()
    conn.validate_connection.assert_called_once_with(
        'S1', force_reconnect=False
    )

    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )
    comp._run_adb('echo hi')
    mock_exec.assert_called_once_with(
        command='echo hi',
        comm_uris=['10.0.0.1:5555'],
        shell=True,
        subprocess_check_flag=False,
        capture_output=False,
        gateway=None,
    )
