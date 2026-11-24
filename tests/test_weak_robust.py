"""Weak Robust Equivalence Class Testing (EECS 4313 / Jorgensen) test suite.

Each target is split into two parametrized functions:
- `test_<target>_weak_robust_valid`: Weak Normal Core (max(|V_i|) cases)
- `test_<target>_weak_robust_invalid`: Single-Fault Robust cases (sum(|I_i|) cases)
with semantic traceable IDs and strict `pytest.raises(..., match=...)` oracles.
"""

import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.adb_executor import execute_adb_command
from device_manager.components.object_manager import ObjectManager
from device_manager.connection.device_connection import DeviceConnection
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo
from device_manager.device_actions import DeviceActions
from device_manager.exceptions.errors import (
    DeviceDisconnectedError,
    DeviceNotFoundError,
    UnexpectedAdbOutputError,
)
from device_manager.manager import DeviceManager
from device_manager.utils.adb_parsers import (
    parse_bool_flag,
    parse_display_orientation,
    parse_screen_dimensions,
)


# ============================================================================
# 1. execute_adb_command — N = max(4, 2, 2, 2) + (1 + 1) = 6
# ============================================================================
class _RecordingGateway:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def run(self, args, *, check=False, capture_output=False, text=None):
        self.calls.append(list(args))
        return subprocess.CompletedProcess(args=list(args), returncode=0, stdout='ok')


@pytest.mark.parametrize(
    'command, comm_uris, shell, capture_output, expected_calls',
    [
        pytest.param(
            'input tap 10 20',
            ['emulator-5554'],
            True,
            False,
            [['adb', '-s', 'emulator-5554', 'shell', 'input', 'tap', '10', '20']],
            id='[Vcmd1,Vuri1,Vsh2,Vcap1]-shell_tap_single_device',
        ),
        pytest.param(
            'adb devices',
            ['emulator-5554', '192.168.1.10:5555'],
            False,
            True,
            [
                ['adb', '-s', 'emulator-5554', 'devices'],
                ['adb', '-s', '192.168.1.10:5555', 'devices'],
            ],
            id='[Vcmd2,Vuri2,Vsh1,Vcap2]-strip_adb_prefix_multi_device',
        ),
        pytest.param(
            'shell ls',
            ['emulator-5554'],
            True,
            True,
            [['adb', '-s', 'emulator-5554', 'shell', 'ls']],
            id='[Vcmd3,Vuri1,Vsh2,Vcap2]-existing_shell_prefix_not_duplicated',
        ),
        pytest.param(
            'pull "/sdcard/my file.png" "/tmp/out dir"',
            ['emulator-5554'],
            False,
            False,
            [['adb', '-s', 'emulator-5554', 'pull', '/sdcard/my file.png', '/tmp/out dir']],
            id='[Vcmd4,Vuri1,Vsh1,Vcap1]-quoted_paths_with_spaces',
        ),
    ],
)
def test_execute_adb_command_weak_robust_valid(
    command: str,
    comm_uris: list[str],
    shell: bool,
    capture_output: bool,
    expected_calls: list[list[str]],
) -> None:
    gateway = _RecordingGateway()
    result = execute_adb_command(
        command=command,
        comm_uris=comm_uris,
        shell=shell,
        capture_output=capture_output,
        gateway=gateway,
    )
    assert result.returncode == 0
    assert gateway.calls == expected_calls


@pytest.mark.parametrize(
    'command, comm_uris, shell, expected_exc, match_pattern',
    [
        pytest.param(
            'input tap 10 20',
            [],
            True,
            ValueError,
            r'No devices specified for command execution\.',
            id='[Vcmd1,Iuri1,Vsh2]-empty_comm_uris',
        ),
        pytest.param(
            'pull "/sdcard/unclosed',
            ['emulator-5554'],
            False,
            ValueError,
            r'No closing quotation',
            id='[Icmd1,Vuri1,Vsh1]-malformed_quoted_command',
        ),
    ],
)
def test_execute_adb_command_weak_robust_invalid(
    command: str,
    comm_uris: list[str],
    shell: bool,
    expected_exc: type[Exception],
    match_pattern: str,
) -> None:
    gateway = _RecordingGateway()
    with pytest.raises(expected_exc, match=match_pattern):
        execute_adb_command(
            command=command,
            comm_uris=comm_uris,
            shell=shell,
            gateway=gateway,
        )


# ============================================================================
# 2. DeviceActions.set_location_mode — N = max(4, 1) + (3 + 1) = 8
# ============================================================================
@pytest.mark.parametrize(
    'mode, expected_cmd',
    [
        pytest.param('0', 'settings put secure location_mode 0', id='[Vm0,Vc1]-mode_off'),
        pytest.param('1', 'settings put secure location_mode 1', id='[Vm1,Vc1]-mode_sensors_only'),
        pytest.param('2', 'settings put secure location_mode 2', id='[Vm2,Vc1]-mode_battery_saving'),
        pytest.param('3', 'settings put secure location_mode 3', id='[Vm3,Vc1]-mode_high_accuracy'),
    ],
)
def test_set_location_mode_weak_robust_valid(
    mode: str,
    expected_cmd: str,
    mocker: MockerFixture,
) -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    conn.validate_connection.return_value = True
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command'
    )

    actions = DeviceActions(conn, 'emulator-5554')
    actions.set_location_mode(mode)

    mock_exec.assert_called_once()
    assert mock_exec.call_args.kwargs['command'] == expected_cmd


@pytest.mark.parametrize(
    'mode, connected, expected_exc, match_pattern',
    [
        pytest.param(
            '-1',
            True,
            ValueError,
            r"Invalid mode\. Valid values are '0', '1', '2', '3'\.",
            id='[Im1,Vc1]-mode_below_min',
        ),
        pytest.param(
            '4',
            True,
            ValueError,
            r"Invalid mode\. Valid values are '0', '1', '2', '3'\.",
            id='[Im2,Vc1]-mode_above_max',
        ),
        pytest.param(
            '',
            True,
            ValueError,
            r"Invalid mode\. Valid values are '0', '1', '2', '3'\.",
            id='[Im3,Vc1]-mode_empty_string',
        ),
        pytest.param(
            '3',
            False,
            DeviceDisconnectedError,
            r'Device connection is not valid\.',
            id='[Vm3,Ic1]-device_disconnected',
        ),
    ],
)
def test_set_location_mode_weak_robust_invalid(
    mode: str,
    connected: bool,
    expected_exc: type[Exception],
    match_pattern: str,
) -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'emulator-5554'
    conn.validate_connection.return_value = connected

    actions = DeviceActions(conn, 'emulator-5554')
    with pytest.raises(expected_exc, match=match_pattern):
        actions.set_location_mode(mode)


# ============================================================================
# 3. ObjectManager.add — N = max(2, 1) + (2 + 1) = 5
# ============================================================================
@pytest.mark.parametrize(
    'key, value',
    [
        pytest.param('dev1', 10, id='[Vk1,Vo1]-nominal_string_key_int_value'),
        pytest.param('', 20, id='[Vk2,Vo1]-empty_string_key_int_value'),
    ],
)
def test_object_manager_add_weak_robust_valid(key: str, value: int) -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('seed', 1)
    manager.add(key, value)
    assert manager[key] == value


@pytest.mark.parametrize(
    'key, value, expected_exc, match_pattern',
    [
        pytest.param(
            123,
            10,
            TypeError,
            r"Key of type <class 'int'> not allowed",
            id='[Ik1,Vo1]-int_key',
        ),
        pytest.param(
            None,
            10,
            TypeError,
            r"Key of type <class 'NoneType'> not allowed",
            id='[Ik2,Vo1]-none_key',
        ),
        pytest.param(
            'dev2',
            'not-an-int',
            TypeError,
            r"Object of type <class 'str'> not allowed",
            id='[Vk1,Io1]-heterogeneous_value_type',
        ),
    ],
)
def test_object_manager_add_weak_robust_invalid(
    key: object,
    value: object,
    expected_exc: type[Exception],
    match_pattern: str,
) -> None:
    manager: ObjectManager[int] = ObjectManager()
    manager.add('seed', 1)
    with pytest.raises(expected_exc, match=match_pattern):
        manager.add(key, value)  # type: ignore[arg-type]


# ============================================================================
# 4. ADB Parsers — parse_bool_flag (N=5), parse_screen_dimensions (N=3),
#    parse_display_orientation (N=6)
# ============================================================================
@pytest.mark.parametrize(
    'output, key, expected',
    [
        pytest.param('  mScreenOn=true\n', 'mScreenOn', True, id='[Vout1,Vk1]-flag_true'),
        pytest.param('  mScreenOn=false\n', 'mScreenOn', False, id='[Vout2,Vk1]-flag_false'),
    ],
)
def test_parse_bool_flag_weak_robust_valid(
    output: str,
    key: str,
    expected: bool,
) -> None:
    assert parse_bool_flag(output, key) is expected


@pytest.mark.parametrize(
    'output, key, expected_exc, match_pattern',
    [
        pytest.param(
            '  otherFlag=true\n',
            'mScreenOn',
            UnexpectedAdbOutputError,
            r'Unexpected output from ADB command',
            id='[Iout1,Vk1]-missing_key',
        ),
        pytest.param(
            '  mScreenOn=true\n  mScreenOn=false\n',
            'mScreenOn',
            UnexpectedAdbOutputError,
            r'Unexpected output from ADB command',
            id='[Iout2,Vk1]-duplicate_key_lines',
        ),
        pytest.param(
            '  mScreenOn=unknown\n',
            'mScreenOn',
            UnexpectedAdbOutputError,
            r'Unexpected output from ADB command',
            id='[Iout3,Vk1]-non_boolean_value',
        ),
    ],
)
def test_parse_bool_flag_weak_robust_invalid(
    output: str,
    key: str,
    expected_exc: type[Exception],
    match_pattern: str,
) -> None:
    with pytest.raises(expected_exc, match=match_pattern):
        parse_bool_flag(output, key)


@pytest.mark.parametrize(
    'output, expected',
    [
        pytest.param('Physical size: 1080x2400\n', (1080, 2400), id='[Vout1]-standard_fhd'),
    ],
)
def test_parse_screen_dimensions_weak_robust_valid(
    output: str,
    expected: tuple[int, int],
) -> None:
    assert parse_screen_dimensions(output) == expected


@pytest.mark.parametrize(
    'output, expected_exc, match_pattern',
    [
        pytest.param(
            'Override size: 720x1280\n',
            UnexpectedAdbOutputError,
            r'Unexpected output from ADB command',
            id='[Iout1]-missing_physical_size',
        ),
        pytest.param(
            '',
            UnexpectedAdbOutputError,
            r'Unexpected output from ADB command',
            id='[Iout2]-empty_output',
        ),
    ],
)
def test_parse_screen_dimensions_weak_robust_invalid(
    output: str,
    expected_exc: type[Exception],
    match_pattern: str,
) -> None:
    with pytest.raises(expected_exc, match=match_pattern):
        parse_screen_dimensions(output)


@pytest.mark.parametrize(
    'output, expected',
    [
        pytest.param('  mCurrentOrientation=0\n', 'Portrait', id='[V0]-portrait'),
        pytest.param('  mCurrentOrientation=1\n', 'Landscape', id='[V1]-landscape'),
        pytest.param('  mCurrentOrientation=2\n', 'Reverse Portrait', id='[V2]-reverse_portrait'),
        pytest.param('  mCurrentOrientation=3\n', 'Reverse Landscape', id='[V3]-reverse_landscape'),
        pytest.param('  mCurrentOrientation=9\n', 'Unknown', id='[V4]-unmapped_code'),
    ],
)
def test_parse_display_orientation_weak_robust_valid(
    output: str,
    expected: str,
) -> None:
    assert parse_display_orientation(output) == expected


@pytest.mark.parametrize(
    'output, expected_exc, match_pattern',
    [
        pytest.param(
            'DisplayDeviceInfo{no orientation}\n',
            UnexpectedAdbOutputError,
            r'Unexpected output from ADB command',
            id='[Iout1]-missing_orientation_field',
        ),
    ],
)
def test_parse_display_orientation_weak_robust_invalid(
    output: str,
    expected_exc: type[Exception],
    match_pattern: str,
) -> None:
    with pytest.raises(expected_exc, match=match_pattern):
        parse_display_orientation(output)


# ============================================================================
# 5. DeviceConnection.stop_connection — N = max(3) + 2 = 5
# ============================================================================
@pytest.mark.parametrize(
    'selected, adb_stdout_prefix, expected_result',
    [
        pytest.param(['WIFI1'], 'disconnected', True, id='[Vd1,Vr1]-single_disconnect_ok'),
        pytest.param(['WIFI1', 'WIFI2'], 'disconnected', True, id='[Vd2,Vr1]-multi_disconnect_ok'),
        pytest.param(['WIFI1'], 'error: no such device', False, id='[Vd1,Vr2]-disconnect_failed'),
    ],
)
def test_stop_connection_weak_robust_valid(
    selected: list[str],
    adb_stdout_prefix: str,
    expected_result: bool,
    mocker: MockerFixture,
) -> None:
    mocker.patch('device_manager.connection.device_connection.ConnectionManager')
    mocker.patch('device_manager.connection.device_connection.UsbDeviceScanner')

    class FakeGateway:
        def run(self, args, *, check=False, capture_output=False, text=None):
            uri = args[2]
            stdout = (
                f'disconnected {uri}\n'
                if adb_stdout_prefix == 'disconnected'
                else f'{adb_stdout_prefix} {uri}\n'
            )
            return subprocess.CompletedProcess(args=list(args), returncode=0, stdout=stdout)

    dc = DeviceConnection(gateway=FakeGateway())
    dc.connection_info.add('WIFI1', ServiceInfo('WIFI1', '10.0.0.1', 5555, ConnectionType.WIFI))
    dc.connection_info.add('WIFI2', ServiceInfo('WIFI2', '10.0.0.2', 5555, ConnectionType.WIFI))

    assert dc.stop_connection(selected) is expected_result


@pytest.mark.parametrize(
    'selected, expected_exc, match_pattern',
    [
        pytest.param(
            [],
            ValueError,
            r'No devices selected to disconnect',
            id='[Id1]-empty_device_list',
        ),
        pytest.param(
            ['UNKNOWN'],
            DeviceNotFoundError,
            r'device was not found',
            id='[Id2]-unregistered_serial',
        ),
    ],
)
def test_stop_connection_weak_robust_invalid(
    selected: list[str],
    expected_exc: type[Exception],
    match_pattern: str,
    mocker: MockerFixture,
) -> None:
    mocker.patch('device_manager.connection.device_connection.ConnectionManager')
    mocker.patch('device_manager.connection.device_connection.UsbDeviceScanner')
    dc = DeviceConnection()
    with pytest.raises(expected_exc, match=match_pattern):
        dc.stop_connection(selected)


# ============================================================================
# 6. DeviceManager.execute_adb_command — N = max(3) + 3 = 6
# ============================================================================
@pytest.mark.parametrize(
    'comm_uris, expected_uris',
    [
        pytest.param(None, ['USB1'], id='[Vu1]-none_resolves_connected_devices'),
        pytest.param(['USB1'], ['USB1'], id='[Vu2]-explicit_list'),
        pytest.param(('USB1',), ('USB1',), id='[Vu3]-explicit_tuple'),
    ],
)
def test_device_manager_execute_adb_command_weak_robust_valid(
    comm_uris: list[str] | tuple[str, ...] | None,
    expected_uris: list[str] | tuple[str, ...],
    mocker: MockerFixture,
) -> None:
    usb_service = ServiceInfo('USB1', '', 0, ConnectionType.USB)
    conn = MagicMock()
    conn.usb_scanner.list_connected_devices.return_value = [usb_service]
    conn.connection_info.get.return_value = usb_service
    conn.build_comm_uri.return_value = 'USB1'

    mock_exec = mocker.patch('device_manager.manager.execute_adb_command')
    dm = DeviceManager(check_dependencies=False, connector=conn)
    dm.execute_adb_command('input keyevent 3', comm_uris=comm_uris)  # type: ignore[arg-type]

    assert mock_exec.call_args.kwargs['comm_uris'] == expected_uris


@pytest.mark.parametrize(
    'comm_uris, expected_exc, match_pattern',
    [
        pytest.param(
            'USB1',
            TypeError,
            r'comm_uris must be a list, tuple or None',
            id='[Iu1]-str_instead_of_sequence',
        ),
        pytest.param(
            123,
            TypeError,
            r'comm_uris must be a list, tuple or None',
            id='[Iu2]-int_instead_of_sequence',
        ),
        pytest.param(
            [],
            ValueError,
            r'No devices specified for command execution\.',
            id='[Iu3]-empty_list',
        ),
    ],
)
def test_device_manager_execute_adb_command_weak_robust_invalid(
    comm_uris: object,
    expected_exc: type[Exception],
    match_pattern: str,
) -> None:
    conn = MagicMock()
    conn.usb_scanner.list_connected_devices.return_value = []
    dm = DeviceManager(check_dependencies=False, connector=conn)

    with pytest.raises(expected_exc, match=match_pattern):
        dm.execute_adb_command('input keyevent 3', comm_uris=comm_uris)  # type: ignore[arg-type]


def test_parse_getprop_preserves_colons_in_values_and_all_base_keys() -> None:
    from device_manager.utils.adb_parsers import parse_getprop

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


def test_qrcode_defaults_and_rebuild_parameters(mocker) -> None:
    import qrcode.constants

    from device_manager.utils.qrcode import QRCode

    qr = QRCode(qrcode_data='HELLO-QR')
    assert qr.qrcode_string == 'HELLO-QR'
    assert qr.qrcode_object.version == 1
    assert qr.qrcode_object.error_correction == qrcode.constants.ERROR_CORRECT_L
    assert qr.qrcode_object.box_size == 20
    assert qr.qrcode_object.border == 2
    img1 = qr.qr_image
    assert img1 is not None

    qr.qrcode_string = 'UPDATED-QR-LONGER-PAYLOAD-1234567890'
    assert qr.qrcode_string == 'UPDATED-QR-LONGER-PAYLOAD-1234567890'
    assert qr.qr_image is not img1

    # Verify default fill_color/back_color and custom colors passed to make_image
    mock_qr_cls = mocker.patch('device_manager.utils.qrcode.qrcode.QRCode')
    mock_qr_inst = mock_qr_cls.return_value
    QRCode(qrcode_data='COLOR-DEFAULT')
    mock_qr_cls.assert_called_once_with(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=20,
        border=2,
    )
    mock_qr_inst.add_data.assert_called_once_with('COLOR-DEFAULT')
    mock_qr_inst.make_image.assert_called_once_with(
        fill_color='black',
        back_color='white',
    )


def test_device_prompt_cli_exact_prompts_and_console_outputs(mocker) -> None:
    from unittest.mock import MagicMock

    from rich.console import Console

    from device_manager.cli.device_prompt import DevicePromptCLI
    from device_manager.connection.utils.connection_type import ConnectionType
    from device_manager.connection.utils.service_info import ServiceInfo

    conn = MagicMock()
    cli_default = DevicePromptCLI(conn)
    assert isinstance(cli_default.console, Console)

    console = MagicMock()
    cli = DevicePromptCLI(conn, console=console)

    mock_prompt = mocker.patch(
        'device_manager.cli.device_prompt.Prompt'
    ).return_value
    mock_prompt.ask.return_value = 'n'
    conn.device_pairing.return_value = True
    cli.check_pairing()
    mock_prompt.ask.assert_called_once_with(
        'Device already paired with host?',
        choices=['Y', 'N'],
        case_sensitive=False,
    )
    conn.device_pairing.assert_called_once_with(5)
    assert console.print.call_args_list == [
        mocker.call('Scan QRCode to pair and close window'),
        mocker.call('Success in pairing new host!'),
    ]

    console.print.reset_mock()
    conn.device_pairing.return_value = False
    cli.check_pairing()
    assert console.print.call_args_list == [
        mocker.call('Scan QRCode to pair and close window'),
        mocker.call('Failed in pairing new host!'),
    ]

    # select_devices_to_connect exact prints and prompts
    console.print.reset_mock()
    mock_prompt.ask.reset_mock()
    conn.available_devices.return_value = {
        'SER1': ServiceInfo('SER1', '10.0.0.1', 5555, ConnectionType.WIFI),
    }
    mock_prompt.ask.side_effect = ['0', '1', 'n']
    selected = cli.select_devices_to_connect()
    assert selected == ['SER1']
    console.print.assert_any_call('Available devices found in the network:')
    console.print.assert_any_call('  [1] - SER1 on IP: 10.0.0.1')
    mock_prompt.ask.assert_any_call(
        'Select device index to connect, or 0 to search devices again',
        choices=['1', '0'],
    )
    mock_prompt.ask.assert_any_call(
        'Do you want to connect to another device?',
        choices=['Y', 'N'],
        case_sensitive=False,
    )

    # prompt_device_connection exact prompt
    mock_prompt.ask.reset_mock()
    mock_prompt.ask.side_effect = ['y', 'n', '1', 'n']
    assert cli.prompt_device_connection() == ['SER1']
    mock_prompt.ask.assert_any_call(
        'Do you want to pair another device?',
        choices=['Y', 'N'],
        case_sensitive=False,
    )


def test_qrcode_viewer_and_util_functions_exact_defaults(mocker) -> None:
    import string
    from unittest.mock import MagicMock

    import numpy as np

    from device_manager.cli.qrcode_viewer import show_qr_cli, show_qr_window
    from device_manager.utils.util_functions import create_password, grep

    qr_obj = MagicMock()
    show_qr_cli(qr_obj)
    qr_obj.print_ascii.assert_called_once_with(tty=True)

    qr_img = MagicMock()
    qr_img.save.side_effect = lambda buf: buf.write(b'\x01\x02\x03')
    mock_cv = mocker.patch('device_manager.cli.qrcode_viewer.cv')
    mock_cv.IMREAD_COLOR = 1
    mock_cv.imdecode.return_value = 'decoded'
    mock_cv.resize.return_value = 'resized'

    show_qr_window(qr_img)
    imdecode_args = mock_cv.imdecode.call_args.args
    assert isinstance(imdecode_args[0], np.ndarray)
    assert imdecode_args[0].dtype == np.uint8
    assert imdecode_args[1] == 1
    mock_cv.resize.assert_called_once_with('decoded', (400, 400))
    mock_cv.imshow.assert_called_once_with('QRCode', 'resized')
    mock_cv.waitKey.assert_called_once_with(delay=0)
    mock_cv.destroyAllWindows.assert_called_once()

    pwd = create_password()
    assert len(pwd) == 8
    assert all(ch in string.ascii_letters + string.digits for ch in pwd)
    assert grep('Foo\nbar', 'foo') == []
    assert grep('Foo\nbar', 'foo', ignore_case=True) == ['Foo']
