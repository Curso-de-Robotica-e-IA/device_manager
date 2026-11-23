import subprocess

import pytest
from pytest_mock import MockerFixture

from device_manager.adb_executor import execute_adb_command


def test_execute_adb_command_raises_without_devices() -> None:
    with pytest.raises(ValueError, match='No devices specified'):
        execute_adb_command(command='devices', comm_uris=[])


def test_execute_adb_command_uses_shell_false_and_preserves_quoted_paths(
    mocker: MockerFixture,
) -> None:
    mock_run = mocker.patch(
        'device_manager.adb_executor.subprocess.run',
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout='ok'),
    )

    result = execute_adb_command(
        command='adb pull "/sdcard/My Photos/img 1.png" "/tmp/out dir"',
        comm_uris=['192.168.0.10:5555', 'emulator-5554'],
        shell=False,
        subprocess_check_flag=True,
        capture_output=True,
    )

    assert result.stdout == 'ok'
    assert mock_run.call_count == 2
    first_call_args, first_call_kwargs = mock_run.call_args_list[0]
    assert first_call_args[0] == [
        'adb',
        '-s',
        '192.168.0.10:5555',
        'pull',
        '/sdcard/My Photos/img 1.png',
        '/tmp/out dir',
    ]
    assert first_call_kwargs['shell'] is False
    assert first_call_kwargs['check'] is False
    assert first_call_kwargs['capture_output'] is True
    assert first_call_kwargs['text'] is True


def test_execute_adb_command_prepends_shell_when_requested(
    mocker: MockerFixture,
) -> None:
    mock_run = mocker.patch(
        'device_manager.adb_executor.subprocess.run',
        return_value=subprocess.CompletedProcess(args=[], returncode=0, stdout=''),
    )

    execute_adb_command(
        command='input tap 10 20',
        comm_uris=['emulator-5554'],
        shell=True,
    )

    args, kwargs = mock_run.call_args
    assert args[0] == ['adb', '-s', 'emulator-5554', 'shell', 'input', 'tap', '10', '20']
    assert kwargs['shell'] is False
    assert kwargs['text'] is None
