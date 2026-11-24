import asyncio
import subprocess
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.asyncio_dm.async_adb_pairing import AsyncAdbPairing
from device_manager.asyncio_dm.async_mdns_listener import AsyncMDnsListener
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.service_info import ServiceInfo


def test_async_mdns_listener_updates_service_context() -> None:
    context = MDnsContext()
    listener = AsyncMDnsListener(context)

    zc = MagicMock()
    zc_info = MagicMock()
    zc_info.addresses = [b'\x7f\x00\x00\x01']
    zc_info.port = 5555
    zc_info.name = 'adb-emulator-5555._adb-tls-pairing._tcp.local.'
    zc.async_get_service_info = AsyncMock(return_value=zc_info)

    async def _run() -> None:
        await listener.add_service(zc, '_adb-tls-pairing._tcp.local.', zc_info.name)
        assert 'adb-emulator-5555' in context.get_online_service()

        await listener.update_service(zc, '_adb-tls-pairing._tcp.local.', zc_info.name)
        assert 'adb-emulator-5555' in context.get_online_service()

        await listener.remove_service(zc, '_adb-tls-pairing._tcp.local.', zc_info.name)
        assert 'adb-emulator-5555' in context.get_offline_service()

    asyncio.run(_run())


def test_async_pair_devices_returns_false_when_empty() -> None:
    pairing = AsyncAdbPairing(password='123456')
    assert asyncio.run(pairing.pair_devices()) is False


def test_async_pair_devices_success_and_failure(mocker: MockerFixture) -> None:
    pairing = AsyncAdbPairing(password='123456')
    service = ServiceInfo(
        serial_number='dev1',
        ip='192.168.1.50',
        port=40000,
        connection=ConnectionType.WIFI,
    )
    pairing._context.add_service('dev1', service)

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.communicate = AsyncMock(
        return_value=(b'Successfully paired to 192.168.1.50:40000\n', b''),
    )
    mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.asyncio.create_subprocess_exec',
        new=AsyncMock(return_value=mock_proc),
    )

    assert asyncio.run(pairing.pair_devices()) is True

    mock_proc.communicate = AsyncMock(return_value=(b'Failed\n', b'err'))
    assert asyncio.run(pairing.pair_devices()) is False


def test_async_pair_devices_raises_when_check_flag_enabled(
    mocker: MockerFixture,
) -> None:
    pairing = AsyncAdbPairing(password='123456', subprocess_check_flag=True)
    service = ServiceInfo(
        serial_number='dev1',
        ip='192.168.1.50',
        port=40000,
        connection=ConnectionType.WIFI,
    )
    pairing._context.add_service('dev1', service)

    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.communicate = AsyncMock(return_value=(b'', b'error'))
    mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.asyncio.create_subprocess_exec',
        new=AsyncMock(return_value=mock_proc),
    )

    with pytest.raises(subprocess.CalledProcessError):
        asyncio.run(pairing.pair_devices())


def test_async_adb_pairing_defaults_args_and_logs(
    mocker,
    caplog,
) -> None:
    import asyncio
    import logging
    from unittest.mock import AsyncMock, MagicMock

    from zeroconf import InterfaceChoice

    from device_manager.asyncio_dm.async_adb_pairing import AsyncAdbPairing
    from device_manager.connection.utils.connection_type import ConnectionType
    from device_manager.connection.utils.mdns_listener import (
        PAIRING_SERVICE_TYPE,
    )
    from device_manager.connection.utils.service_info import ServiceInfo

    default_p = AsyncAdbPairing(password='123456')
    assert default_p._name == 'robot-celular'
    assert default_p._subprocess_check_flag is False
    assert default_p._max_zc_instances == 10
    assert default_p.qrcode_string == 'WIFI:T:ADB;S:robot-celular;P:123456;;'

    # _new_zeroconf_instance exact Zeroconf kwargs + zombie boundary
    mock_zc_cls = mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.Zeroconf'
    )
    mock_browser_cls = mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.ServiceBrowser'
    )
    mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.asyncio.sleep',
        new=AsyncMock(),
    )
    mock_sleep = mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.asyncio.sleep',
        new=AsyncMock(),
    )
    mock_listener_cls = mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.AsyncMDnsListener'
    )
    p = AsyncAdbPairing(
        service_name='svc-async',
        service_regex_filter='adb-([A-Z0-9]+)',
        subprocess_check_flag=False,
        password='654321',
        max_zeroconf_instances=1,
    )
    p._zeroconf_zombies = [MagicMock()]

    # update_qrcode and set_password
    old_qr = p.qrcode
    p.update_qrcode(new_password=False)
    assert p.password == '654321'
    assert p.qrcode is not old_qr
    p.set_password('999888', update_qrcode=False)
    assert p.password == '999888'
    p.set_password('654321', update_qrcode=True)
    assert p.qrcode_string == 'WIFI:T:ADB;S:svc-async;P:654321;;'

    async def _run() -> None:
        with caplog.at_level(
            logging.DEBUG,
            logger='device_manager.asyncio_dm.async_adb_pairing',
        ):
            await p.start()
        mock_zc_cls.assert_called_once_with(
            interfaces=InterfaceChoice.Default,
            unicast=False,
            ip_version=None,
            apple_p2p=False,
        )
        mock_listener_cls.assert_called_once_with(
            p._context,
            'adb-([A-Z0-9]+)',
            PAIRING_SERVICE_TYPE,
        )
        assert mock_browser_cls.call_args.args[1] == PAIRING_SERVICE_TYPE
        mock_browser_cls.return_value._async_start.assert_called_once()
        mock_sleep.assert_awaited_once_with(5)
        assert p.service_browser_started is True

        # Invoke finalizer atexit callback directly
        assert p._finalize is not None
        caplog.clear()
        with caplog.at_level(
            logging.DEBUG,
            logger='device_manager.asyncio_dm.async_adb_pairing',
        ):
            p._finalize()
        assert any(
            r.message == 'Finalizing Zeroconf instance.'
            for r in caplog.records
        )
        assert p.browser is None
        assert p.service_browser_started is False

        # pair_devices exact subprocess exec args + INFO and WARNING logs
        p._context.add_service(
            'SER1', ServiceInfo('SER1', '10.0.0.1', 37123, ConnectionType.WIFI)
        )
        fake_proc_ok = MagicMock()
        fake_proc_ok.returncode = 0
        fake_proc_ok.communicate = AsyncMock(
            return_value=(b'Successfully paired to 10.0.0.1:37123\n', b'')
        )
        mock_exec = mocker.patch(
            'device_manager.asyncio_dm.async_adb_pairing.asyncio.create_subprocess_exec',
            new=AsyncMock(return_value=fake_proc_ok),
        )
        with caplog.at_level(
            logging.INFO,
            logger='device_manager.asyncio_dm.async_adb_pairing',
        ):
            assert await p.pair_devices() is True
        mock_exec.assert_called_once_with(
            'adb',
            'pair',
            '10.0.0.1:37123',
            '654321',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert any(
            r.message
            == 'Successfully paired device asynchronously: uri=10.0.0.1:37123'
            for r in caplog.records
        )

        fake_proc_fail = MagicMock()
        fake_proc_fail.returncode = 1
        fake_proc_fail.communicate = AsyncMock(
            return_value=(b'  bad pin  \n', b'err-detail')
        )
        mock_exec.return_value = fake_proc_fail
        with caplog.at_level(
            logging.WARNING,
            logger='device_manager.asyncio_dm.async_adb_pairing',
        ):
            assert await p.pair_devices() is False
        assert any(
            r.message
            == 'Failed to pair device asynchronously: uri=10.0.0.1:37123 output=bad pin'
            for r in caplog.records
        )

        # subprocess_check_flag=True raises CalledProcessError with exact fields
        p._subprocess_check_flag = True
        import subprocess
        import pytest

        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            await p.pair_devices()
        assert exc_info.value.returncode == 1
        assert exc_info.value.cmd == ['adb', 'pair', '10.0.0.1:37123', '654321']
        assert exc_info.value.output == '  bad pin  \n'
        assert exc_info.value.stderr == 'err-detail'

        p._zeroconf.async_close = AsyncMock()
        await p.stop_pair_listener()
        assert p.service_browser_started is False
        assert p.browser is None

    asyncio.run(_run())
