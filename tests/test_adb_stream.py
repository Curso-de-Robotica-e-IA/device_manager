import io
from unittest.mock import MagicMock

import pytest

from device_manager.adb_gateway import AdbutilsAdbGateway
from device_manager.adb_stream import AdbStreamProcess
from device_manager.device_actions import DeviceActions
from device_manager.enumerations.adb_stream import (
    AdbStreamCommand,
    AdbStreamSpec,
    CustomAdbStream,
)
from device_manager.exceptions.errors import DeviceDisconnectedError


def _make_fake_connection(
    lines: list[str] | None = None,
    chunks: list[bytes] | None = None,
) -> MagicMock:
    conn = MagicMock()
    text_payload = ''.join(lines or [])
    conn.conn.makefile.return_value = io.StringIO(text_payload)
    conn.conn.recv.side_effect = list(chunks or [b''])
    return conn


def test_adb_stream_process_iter_lines_and_context_manager() -> None:
    fake_conn = _make_fake_connection(lines=['line1\r\n', 'line2\n'])

    with AdbStreamProcess(fake_conn, command='logcat') as proc:
        assert proc.command == 'logcat'
        assert proc.is_open is True
        assert list(proc.iter_lines()) == ['line1', 'line2']

    assert proc.is_open is False
    fake_conn.close.assert_called_once()

    # Idempotent close / terminate
    proc.terminate()
    fake_conn.close.assert_called_once()


def test_adb_stream_process_stops_iter_lines_when_closed_mid_stream() -> None:
    fake_conn = _make_fake_connection(lines=['a\n', 'b\n', 'c\n'])
    proc = AdbStreamProcess(fake_conn, command='getevent -lt')

    collected: list[str] = []
    for line in proc.iter_lines():
        collected.append(line)
        proc.terminate()

    assert collected == ['a']
    assert proc.is_open is False


def test_adb_stream_process_read_chunks_and_stop_on_close() -> None:
    fake_conn = _make_fake_connection(chunks=[b'abc', b'def', b''])
    proc = AdbStreamProcess(
        fake_conn,
        command='screenrecord --output-format=h264 -',
        encoding=None,
    )
    assert list(proc.read_chunks(chunk_size=3)) == [b'abc', b'def']
    proc.close()
    assert list(proc.read_chunks()) == []


@pytest.mark.parametrize(
    ('spec', 'expected_cmd', 'expected_encoding'),
    [
        (AdbStreamCommand.GETEVENT, 'getevent -lt', 'utf-8'),
        (
            AdbStreamCommand.GETEVENT.with_args('/dev/input/event1'),
            'getevent -lt /dev/input/event1',
            'utf-8',
        ),
        (
            AdbStreamCommand.LOGCAT.with_args('*:E', '-v', 'time'),
            'logcat *:E -v time',
            'utf-8',
        ),
        (AdbStreamCommand.DMESG, 'dmesg -w', 'utf-8'),
        (AdbStreamCommand.TOP.with_args('-d 1'), 'top -b -d 1', 'utf-8'),
        (
            AdbStreamCommand.SCREENRECORD,
            'screenrecord --output-format=h264 -',
            None,
        ),
        (
            CustomAdbStream('  dumpsys battery  '),
            'dumpsys battery',
            'utf-8',
        ),
    ],
)
def test_device_actions_start_stream_polymorphic_specs(
    spec: AdbStreamSpec,
    expected_cmd: str,
    expected_encoding: str | None,
) -> None:
    fake_adb_conn = _make_fake_connection(lines=['ok\n'])
    fake_device = MagicMock()
    fake_device.shell.return_value = fake_adb_conn
    fake_client = MagicMock()
    fake_client.device.return_value = fake_device

    gw = AdbutilsAdbGateway(client=fake_client)
    conn = MagicMock()
    conn.validate_connection.return_value = True
    conn.build_comm_uri.return_value = 'SER-STREAM'

    actions = DeviceActions(conn, 'SER-STREAM', gateway=gw)
    proc = actions.start_stream(spec, timeout=30.0)

    assert isinstance(proc, AdbStreamProcess)
    assert proc.command == expected_cmd
    assert proc._encoding == expected_encoding
    fake_client.device.assert_called_once_with(serial='SER-STREAM')
    fake_device.shell.assert_called_once_with(
        expected_cmd,
        stream=True,
        timeout=30.0,
    )


def test_device_actions_start_stream_custom_class_fallback_and_errors(
    mocker,
) -> None:
    class _BatteryStream:
        def build_command(self) -> str:
            return 'dumpsys battery'

        @property
        def default_encoding(self) -> str | None:
            return 'utf-8'

    conn = MagicMock()
    conn.validate_connection.return_value = True
    conn.build_comm_uri.return_value = 'SER-1'
    actions = DeviceActions(conn, 'SER-1')

    with pytest.raises(TypeError, match='AdbStreamSpec'):
        actions.start_stream('logcat')  # type: ignore[arg-type]

    with pytest.raises(ValueError, match='non-empty command'):
        CustomAdbStream('   ')

    mock_open = mocker.patch.object(
        AdbutilsAdbGateway,
        'open_stream',
        return_value=MagicMock(spec=AdbStreamProcess),
    )
    actions.start_stream(_BatteryStream())
    mock_open.assert_called_once_with(
        serial='SER-1',
        command='dumpsys battery',
        timeout=None,
        encoding='utf-8',
    )

    conn.validate_connection.return_value = False
    with pytest.raises(
        DeviceDisconnectedError, match='Cannot start ADB stream'
    ):
        actions.start_stream(AdbStreamCommand.LOGCAT)
