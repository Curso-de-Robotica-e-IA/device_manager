import builtins
import subprocess
from unittest.mock import MagicMock

import pytest

from device_manager.device_info import DeviceInfo
from device_manager.ui_hierarchy import Uiautomator2Backend


def test_uiautomator2_backend_caches_device_and_extracts_xml() -> None:
    fake_u2_dev = MagicMock()
    fake_u2_dev.dump_hierarchy.side_effect = [
        '<?xml version="1.0"?><hierarchy><node text="OK"/></hierarchy>',
        '',
    ]
    connector = MagicMock(return_value=fake_u2_dev)

    backend = Uiautomator2Backend(connector=connector)
    xml1 = backend.dump_xml('SER1')
    xml2 = backend.dump_xml('SER1')

    assert (
        xml1 == '<?xml version="1.0"?><hierarchy><node text="OK"/></hierarchy>'
    )
    assert xml2 is None
    connector.assert_called_once_with('SER1')
    assert fake_u2_dev.dump_hierarchy.call_count == 2


def test_uiautomator2_backend_lazy_import_success_and_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_u2_dev = MagicMock()
    fake_u2_dev.dump_hierarchy.return_value = (
        '<?xml version="1.0"?><hierarchy/>'
    )
    fake_u2_mod = MagicMock()
    fake_u2_mod.connect.return_value = fake_u2_dev

    monkeypatch.setitem(__import__('sys').modules, 'uiautomator2', fake_u2_mod)
    backend = Uiautomator2Backend()
    assert backend.dump_xml('SER2') == '<?xml version="1.0"?><hierarchy/>'
    fake_u2_mod.connect.assert_called_once_with('SER2')

    # Missing uiautomator2 raises helpful ImportError
    monkeypatch.delitem(
        __import__('sys').modules, 'uiautomator2', raising=False
    )
    real_import = builtins.__import__

    def _blocked_import(name: str, *args: object, **kwargs: object):
        if name == 'uiautomator2':
            raise ImportError('No module named uiautomator2')
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', _blocked_import)
    backend_missing = Uiautomator2Backend()
    with pytest.raises(ImportError, match=r'device_manager\[u2\]'):
        backend_missing.dump_xml('SER3')


def test_device_info_uses_ui_backend_and_falls_back_to_native_adb() -> None:
    conn = MagicMock()
    conn.build_comm_uri.return_value = 'SER1'
    conn.validate_connection.return_value = True

    gw = MagicMock()
    gw.run.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='<?xml version="1.0"?><hierarchy><node text="Native"/></hierarchy>',
        stderr='',
    )

    backend = MagicMock()
    backend.dump_xml.return_value = (
        '<?xml version="1.0"?><hierarchy><node text="Fast"/></hierarchy>'
    )
    info = DeviceInfo(conn, 'SER1', gateway=gw, ui_backend=backend)
    assert info.get_screen_gui_xml() == (
        '<?xml version="1.0"?><hierarchy><node text="Fast"/></hierarchy>'
    )
    gw.run.assert_not_called()

    # Fallback to native ADB when backend returns None
    backend.dump_xml.return_value = None
    assert info.get_screen_gui_xml() == (
        '<?xml version="1.0"?><hierarchy><node text="Native"/></hierarchy>'
    )
    gw.run.assert_called_once()
