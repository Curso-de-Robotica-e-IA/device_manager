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
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout='ok'
        ),
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
        return_value=subprocess.CompletedProcess(
            args=[], returncode=0, stdout=''
        ),
    )

    execute_adb_command(
        command='input tap 10 20',
        comm_uris=['emulator-5554'],
        shell=True,
    )

    args, kwargs = mock_run.call_args
    assert args[0] == [
        'adb',
        '-s',
        'emulator-5554',
        'shell',
        'input',
        'tap',
        '10',
        '20',
    ]
    assert kwargs['shell'] is False
    assert kwargs['text'] is None


def test_execute_adb_command_defaults_and_fallback_gateway(
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    import logging

    with pytest.raises(
        ValueError,
        match=r'^No devices specified for command execution\.$',
    ):
        execute_adb_command('get-state', [])

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
    import logging
    from unittest.mock import MagicMock

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
    with caplog.at_level(
        logging.WARNING, logger='device_manager.adb_executor'
    ):
        execute_adb_command('bad', ['SER1'], capture_output=True, gateway=gw)

    assert any(
        r.message
        == 'ADB command failed: uri=SER1 command=bad returncode=1 duration_ms=500.0 stderr=boom'
        for r in caplog.records
    )
