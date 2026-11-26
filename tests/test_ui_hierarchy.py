import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from device_manager.device_info import DeviceInfo
from device_manager.exceptions.errors import UnsupportedAndroidVersionError
from device_manager.ui_hierarchy import (
    REMOTE_DEX_PATH,
    NativeResidentUiBackend,
)


def test_native_resident_backend_returns_none_when_dex_missing(
    tmp_path: Path,
) -> None:
    backend = NativeResidentUiBackend(dex_path=tmp_path / 'missing.dex')
    assert backend.dump_xml('SER1') is None


def test_native_resident_backend_streams_xml_reuses_session_and_closes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dex = tmp_path / 'dm_ui_dump.dex'
    dex.write_bytes(b'dex')

    fake_conn = MagicMock()
    fake_conn.conn.recv.side_effect = [
        b'<?xml version="1.0"?><hierarchy>',
        b'<node text="OK"/></hierarchy>\n',
        b'',  # EOF on second call triggers close + None
    ]
    fake_device = MagicMock()
    fake_device.shell.side_effect = ['34', fake_conn]
    fake_client = MagicMock()
    fake_client.device.return_value = fake_device

    backend = NativeResidentUiBackend(dex_path=dex, client=fake_client)
    xml = backend.dump_xml('SER1')
    assert (
        xml == '<?xml version="1.0"?><hierarchy><node text="OK"/></hierarchy>'
    )
    fake_device.sync.push.assert_called_once_with(str(dex), REMOTE_DEX_PATH)
    fake_conn.conn.settimeout.assert_called_once_with(5.0)
    fake_conn.conn.sendall.assert_called_with(b'DUMP\n')

    # Second call reuses existing session, hits EOF -> closes & returns None
    assert backend.dump_xml('SER1') is None
    fake_conn.close.assert_called_once()

    # Exception (e.g. TimeoutError) during dump closes session and returns None
    fake_conn_err = MagicMock()
    fake_conn_err.conn.sendall.side_effect = TimeoutError('timed out')
    fake_device.shell.side_effect = ['34', fake_conn_err]
    assert backend.dump_xml('SER1') is None
    fake_conn_err.close.assert_called_once()

    # Incompatible Android SDK (< 21) raises UnsupportedAndroidVersionError
    fake_device.shell.side_effect = ['19']
    with pytest.raises(UnsupportedAndroidVersionError, match='Android API 19'):
        backend.dump_xml('SER_OLD')

    # close() with no args closes all active sessions; absent uri is a no-op
    backend._sessions['SER_A'] = MagicMock()
    backend.close()
    assert backend._sessions == {}
    backend.close('NON_EXISTENT')

    # Lazy adbutils import path
    fake_adbutils = MagicMock()
    fake_adbutils.adb = fake_client
    monkeypatch.setitem(sys.modules, 'adbutils', fake_adbutils)
    lazy_backend = NativeResidentUiBackend(dex_path=dex)
    assert lazy_backend._get_client() is fake_client


def test_device_info_uses_resident_ui_backend_by_default() -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True

    default_info = DeviceInfo(conn, 'SER1')
    assert isinstance(default_info._ui_backend, NativeResidentUiBackend)

    backend = MagicMock()
    backend.dump_xml.return_value = (
        '<?xml version="1.0"?><hierarchy><node text="Fast"/></hierarchy>'
    )
    info = DeviceInfo(conn, 'SER1', ui_backend=backend)
    assert info.get_screen_gui_xml() == (
        '<?xml version="1.0"?><hierarchy><node text="Fast"/></hierarchy>'
    )
    backend.dump_xml.assert_called_once_with('SER1')


def test_native_resident_backend_take_screenshot_and_device_actions_fallback(
    tmp_path: Path,
) -> None:
    import base64
    import subprocess

    from device_manager.device_actions import DeviceActions

    # Missing dex -> None
    missing_backend = NativeResidentUiBackend(dex_path=tmp_path / 'none.dex')
    assert missing_backend.take_screenshot('SER1') is None

    dex = tmp_path / 'dm_ui_dump.dex'
    dex.write_bytes(b'dex')

    png_payload = b'\x89PNG\r\n\x1a\nDATA'
    framed = (
        b'SCREENSHOT\r\nIMG_BEGIN:'
        + base64.b64encode(png_payload)
        + b':IMG_END\r\n'
    )

    fake_conn = MagicMock()
    fake_conn.conn.recv.side_effect = [
        framed[:18],
        framed[18:],
        b'SCREENSHOT\r\nIMG_ERR\r\n',
        b':IMG_END\r\n',  # malformed frame without IMG_BEGIN
        b'',  # EOF
    ]
    fake_device = MagicMock()
    fake_device.shell.side_effect = ['34', fake_conn, '34', fake_conn]
    fake_client = MagicMock()
    fake_client.device.return_value = fake_device

    backend = NativeResidentUiBackend(dex_path=dex, client=fake_client)
    assert backend.take_screenshot('SER1') == png_payload
    assert backend.take_screenshot('SER1') is None  # ERR
    assert backend.take_screenshot('SER1') is None  # malformed frame
    assert backend.take_screenshot('SER1') is None  # EOF

    # Exception during screenshot closes session and returns None
    fake_conn_err = MagicMock()
    fake_conn_err.conn.sendall.side_effect = TimeoutError('timeout')
    fake_device.shell.side_effect = ['34', fake_conn_err]
    assert backend.take_screenshot('SER1') is None

    # UnsupportedAndroidVersionError propagates
    fake_device.shell.side_effect = ['19']
    with pytest.raises(UnsupportedAndroidVersionError, match='Android API 19'):
        backend.take_screenshot('SER_OLD')

    # DeviceActions.safe_screencap_bytes uses ui_backend first, falls back to exec-out
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=b'\x89PNG_FALLBACK', stderr=b''
    )
    ui_mock = MagicMock()
    ui_mock.take_screenshot.return_value = png_payload
    actions = DeviceActions(conn, 'SER1', gateway=gw, ui_backend=ui_mock)
    assert actions.safe_screencap_bytes() == png_payload
    ui_mock.take_screenshot.assert_called_with('SER1', fmt='jpeg')
    assert actions.safe_screencap_bytes(raw=True) == png_payload
    ui_mock.take_screenshot.assert_called_with('SER1', fmt='png')
    gw.run.assert_not_called()

    ui_mock.take_screenshot.return_value = None
    assert actions.safe_screencap_bytes() == b'\x89PNG_FALLBACK'
    gw.run.assert_called_once()


def test_native_resident_backend_save_screenshot_and_device_actions(
    tmp_path: Path,
) -> None:
    import subprocess

    from device_manager.device_actions import DeviceActions

    missing_backend = NativeResidentUiBackend(dex_path=tmp_path / 'none.dex')
    assert missing_backend.save_screenshot('SER1', '/sdcard/a.jpg') is False

    dex = tmp_path / 'dm_ui_dump.dex'
    dex.write_bytes(b'dex')

    fake_conn = MagicMock()
    fake_conn.conn.recv.side_effect = [
        b'SCREENSHOT_FILE /sdcard/a.jpg\r\n',
        b'FILE_OK\r\n',
        b'FILE_ERR\r\n',
        b'',  # EOF
    ]
    fake_device = MagicMock()
    fake_device.shell.side_effect = ['34', fake_conn]
    fake_client = MagicMock()
    fake_client.device.return_value = fake_device

    backend = NativeResidentUiBackend(dex_path=dex, client=fake_client)
    assert backend.save_screenshot('SER1', '/sdcard/a.jpg') is True
    assert backend.save_screenshot('SER1', '/sdcard/a.jpg') is False
    assert backend.save_screenshot('SER1', '/sdcard/a.jpg') is False

    fake_conn_err = MagicMock()
    fake_conn_err.conn.sendall.side_effect = TimeoutError('timeout')
    fake_device.shell.side_effect = ['34', fake_conn_err]
    assert backend.save_screenshot('SER1', '/sdcard/a.jpg') is False

    fake_device.shell.side_effect = ['19']
    with pytest.raises(UnsupportedAndroidVersionError, match='Android API 19'):
        backend.save_screenshot('SER_OLD', '/sdcard/a.jpg')

    # DeviceActions.screen_shot uses save_screenshot when raw=False, falls back on False/raw=True
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True
    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[], returncode=0, stdout='', stderr=''
    )
    ui_mock = MagicMock()
    ui_mock.save_screenshot.return_value = True
    actions = DeviceActions(conn, 'SER1', gateway=gw, ui_backend=ui_mock)
    actions.screen_shot('shot', '/sdcard')
    ui_mock.save_screenshot.assert_called_once_with('SER1', '/sdcard/shot.jpg')
    gw.run.assert_not_called()

    actions.screen_shot('shot', '/sdcard', raw=True)
    gw.run.assert_called_once()

    gw.run.reset_mock()
    ui_mock.save_screenshot.return_value = False
    actions.screen_shot('shot', '/sdcard', raw=False)
    gw.run.assert_called_once()
