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
