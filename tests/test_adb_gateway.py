"""Unit tests for AdbutilsAdbGateway covering 100% of statements and branches."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.adb_gateway import AdbutilsAdbGateway


def test_adbutils_gateway_lazy_client_and_fallback_paths(
    mocker: MockerFixture,
) -> None:
    fallback = MagicMock()
    fallback.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='fallback'
    )

    # Non-adb / empty command delegates directly to fallback
    gw = AdbutilsAdbGateway(client=MagicMock(), fallback=fallback)
    assert gw.run([]).stdout == 'fallback'
    assert gw.run(['echo', 'hi']).stdout == 'fallback'

    # Lazy import of adbutils.adb when client is None
    fake_adb = MagicMock()
    fake_adb.list.return_value = [
        SimpleNamespace(serial='SER-1', state='device')
    ]
    mocker.patch('adbutils.adb', fake_adb)
    lazy_gw = AdbutilsAdbGateway(fallback=fallback)

    res_text = lazy_gw.run(['adb', 'devices'], capture_output=True, text=True)
    assert res_text.returncode == 0
    assert 'SER-1\tdevice' in res_text.stdout

    res_bytes = lazy_gw.run(
        ['adb', 'devices'], capture_output=True, text=False
    )
    assert res_bytes.stdout == b'List of devices attached\nSER-1\tdevice\n'
    assert res_bytes.stderr == b''

    # Unsupported adb command falls back to SubprocessAdbGateway
    assert lazy_gw.run(['adb', 'start-server']).stdout == 'fallback'
    assert (
        lazy_gw.run(['adb', '-s', 'SER-1', 'tcpip', '5555']).stdout
        == 'fallback'
    )


def test_adbutils_gateway_device_operations() -> None:
    fake_device = MagicMock()
    fake_device.shell.side_effect = ['ok\n', b'\x89PNG']
    fake_client = MagicMock()
    fake_client.device.return_value = fake_device
    fallback = MagicMock()
    gw = AdbutilsAdbGateway(client=fake_client, fallback=fallback)

    # shell
    res_shell = gw.run(['adb', '-s', 'SER-1', 'shell', 'ls', '-l'])
    assert res_shell.returncode == 0
    assert res_shell.stdout == 'ok\n'

    # exec-out
    res_exec = gw.run(['adb', '-s', 'SER-1', 'exec-out', 'screencap', '-p'])
    assert res_exec.returncode == 0
    assert res_exec.stdout == b'\x89PNG'

    # push
    res_push = gw.run(['adb', '-s', 'SER-1', 'push', 'a.txt', '/sdcard/a.txt'])
    assert res_push.returncode == 0
    fake_device.sync.push.assert_called_once_with('a.txt', '/sdcard/a.txt')

    # pull
    res_pull = gw.run(['adb', '-s', 'SER-1', 'pull', '/sdcard/a.txt', 'a.txt'])
    assert res_pull.returncode == 0
    fake_device.sync.pull.assert_called_once_with('/sdcard/a.txt', 'a.txt')


def test_adbutils_gateway_error_handling() -> None:
    fake_client = MagicMock()
    fake_client.device.side_effect = RuntimeError('adb server down')
    gw = AdbutilsAdbGateway(client=fake_client)

    with pytest.raises(subprocess.CalledProcessError):
        gw.run(['adb', '-s', 'SER-1', 'shell', 'ls'], check=True)

    res_txt = gw.run(['adb', '-s', 'SER-1', 'shell', 'ls'], text=True)
    assert res_txt.returncode == 1
    assert res_txt.stdout == ''
    assert 'adb server down' in res_txt.stderr

    res_bin = gw.run(['adb', '-s', 'SER-1', 'shell', 'ls'], text=False)
    assert res_bin.returncode == 1
    assert res_bin.stdout == b''
    assert b'adb server down' in res_bin.stderr


def test_adbutils_gateway_exact_args_outputs_and_edge_fallbacks() -> None:
    fallback = MagicMock()
    fallback.run.return_value = subprocess.CompletedProcess(
        args=['fallback'], returncode=0, stdout='fb', stderr=''
    )
    fake_device = MagicMock()
    fake_device.shell.side_effect = ['out\n', b'RAW']
    fake_client = MagicMock()
    fake_client.list.return_value = [
        SimpleNamespace(serial='S1', state='device'),
        SimpleNamespace(serial='S2', state='offline'),
    ]
    fake_client.device.return_value = fake_device

    gw = AdbutilsAdbGateway(client=fake_client, fallback=fallback)

    gw.run(['ls', '-l'], check=True, capture_output=True, text=True)
    fallback.run.assert_called_with(
        ['ls', '-l'], check=True, capture_output=True, text=True
    )

    r_dev = gw.run(['adb', 'devices'], capture_output=True, text=True)
    assert r_dev.args == ['adb', 'devices']
    assert r_dev.returncode == 0
    assert r_dev.stdout == 'List of devices attached\nS1\tdevice\nS2\toffline\n'
    assert r_dev.stderr == ''

    r_sh = gw.run(['adb', '-s', 'S1', 'shell', 'echo', 'hi'])
    fake_client.device.assert_called_with(serial='S1')
    fake_device.shell.assert_any_call(['echo', 'hi'])
    assert r_sh.args == ['adb', '-s', 'S1', 'shell', 'echo', 'hi']
    assert r_sh.stdout == 'out\n'
    assert r_sh.stderr == ''

    r_ex = gw.run(['adb', '-s', 'S1', 'exec-out', 'screencap', '-p'])
    fake_device.shell.assert_any_call(['screencap', '-p'], encoding=None)
    assert r_ex.args == ['adb', '-s', 'S1', 'exec-out', 'screencap', '-p']
    assert r_ex.stdout == b'RAW'
    assert r_ex.stderr == b''

    r_push = gw.run(['adb', '-s', 'S1', 'push', 'src.txt', '/sdcard/dst.txt'])
    fake_device.sync.push.assert_called_once_with('src.txt', '/sdcard/dst.txt')
    assert r_push.args == ['adb', '-s', 'S1', 'push', 'src.txt', '/sdcard/dst.txt']
    assert r_push.stdout == '' and r_push.stderr == ''

    r_pull = gw.run(['adb', '-s', 'S1', 'pull', '/sdcard/dst.txt', 'out.txt'])
    fake_device.sync.pull.assert_called_once_with('/sdcard/dst.txt', 'out.txt')
    assert r_pull.args == ['adb', '-s', 'S1', 'pull', '/sdcard/dst.txt', 'out.txt']
    assert r_pull.stdout == '' and r_pull.stderr == ''

    for cmd in (
        ['adb', '-s', 'S1', 'shell'],
        ['adb', '-s', 'S1', 'exec-out'],
        ['adb', '-s', 'S1', 'push', 'only_one'],
        ['adb', '-s', 'S1', 'pull', 'only_one'],
    ):
        fallback.run.reset_mock()
        assert gw.run(cmd, check=True, capture_output=True, text=False).stdout == 'fb'
        fallback.run.assert_called_once_with(
            cmd, check=True, capture_output=True, text=False
        )

    fake_client.device.side_effect = RuntimeError('boom')
    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        gw.run(['adb', '-s', 'S1', 'shell', 'ls'], check=True)
    assert exc_info.value.returncode == 1
    assert exc_info.value.cmd == ['adb', '-s', 'S1', 'shell', 'ls']
    assert exc_info.value.output == ''
    assert exc_info.value.stderr == 'boom'
