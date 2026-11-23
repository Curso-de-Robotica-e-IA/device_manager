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
