"""Weak Robust Equivalence Class tests for asyncio_dm (AsyncZeroconf & AsyncAdbPairing)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.asyncio_dm.async_adb_pairing import AsyncAdbPairing
from device_manager.asyncio_dm.async_zeroconf import AsyncZeroconf
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.connection.utils.service_info import ServiceInfo


# ============================================================================
# 1. AsyncZeroconf Proxy — Weak Robust
# ============================================================================
def test_async_zeroconf_proxy_delegation(mocker: MockerFixture) -> None:
    mock_azc_cls = mocker.patch('device_manager.asyncio_dm.async_zeroconf.AZc')
    inner = mock_azc_cls.return_value
    inner.zeroconf = MagicMock()
    inner.zeroconf.only_on_zc = 'zc_val'
    inner.only_on_azc = 'azc_val'
    inner.async_get_service_info = AsyncMock(return_value='svc_info')
    inner.async_close = AsyncMock()

    proxy = AsyncZeroconf(zc=MagicMock())
    assert proxy.zeroconf is inner.zeroconf
    assert proxy.only_on_azc == 'azc_val'

    del inner.only_on_zc
    assert proxy.only_on_zc == 'zc_val'

    async def _run() -> None:
        assert (
            await proxy.async_get_service_info('_t._tcp.local.', 'name')
            == 'svc_info'
        )
        await proxy.async_close()

    asyncio.run(_run())
    inner.async_close.assert_awaited_once()


# ============================================================================
# 2. AsyncAdbPairing — Weak Robust (Valid + Single-Fault Invalid)
# ============================================================================
def test_async_adb_pairing_properties_and_qrcode(
    mocker: MockerFixture,
) -> None:
    pairing = AsyncAdbPairing(password='INITPASS')
    assert pairing.service_browser_started is False
    assert pairing.browser is None
    assert pairing.zeroconf_status is False
    assert pairing.password == 'INITPASS'
    assert 'P:INITPASS;;' in pairing.qrcode_string
    assert pairing.qrcode is not None
    assert pairing.qrcode_image is not None
    assert pairing.has_device_to_pairing() is False

    pairing._context.add_service(
        'dev1',
        ServiceInfo('dev1', '10.0.0.2', 5555, ConnectionType.WIFI),
    )
    assert pairing.has_device_to_pairing() is True

    mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.create_password',
        return_value='ROTATED',
    )
    pairing.update_qrcode(new_password=True)
    assert pairing.password == 'ROTATED'

    pairing.set_password('EXPLICIT', update_qrcode=True)
    assert pairing.password == 'EXPLICIT'
    pairing.set_password('NO_UPDATE', update_qrcode=False)
    assert pairing.password == 'NO_UPDATE'


def test_async_adb_pairing_start_stop_and_zombies(
    mocker: MockerFixture,
) -> None:
    mocker.patch('device_manager.asyncio_dm.async_adb_pairing.Zeroconf')
    mock_azc_cls = mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.AsyncZeroconf'
    )
    mock_azc = mock_azc_cls.return_value
    mock_azc.async_close = AsyncMock()
    mock_browser_cls = mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.ServiceBrowser'
    )
    mock_fin = mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.finalize'
    )
    mock_fin.return_value.alive = True
    mocker.patch(
        'device_manager.asyncio_dm.async_adb_pairing.asyncio.sleep',
        new=AsyncMock(),
    )

    pairing = AsyncAdbPairing(password='123456', max_zeroconf_instances=1)

    async def _run() -> None:
        await pairing.start()
        assert pairing.service_browser_started is True
        assert pairing.zeroconf_status is True
        assert pairing.browser is mock_browser_cls.return_value

        # Idempotent second start
        await pairing.start()
        assert mock_browser_cls.call_count == 1

        # Trigger atexit callback
        atexit_cb = mock_fin.call_args[0][1]
        atexit_cb()
        assert pairing.service_browser_started is False
        assert pairing.browser is None

        # Restart moves previous zeroconf to zombies
        await pairing.start()
        assert len(pairing._zeroconf_zombies) == 1

        await pairing.stop_pair_listener()
        mock_azc.async_close.assert_awaited_once()
        assert pairing.service_browser_started is False

    asyncio.run(_run())


@pytest.mark.parametrize(
    ('scenario', 'expected_exc', 'match_pattern'),
    [
        pytest.param(
            'stop_before_start',
            AttributeError,
            r'zeroconf not configured',
            id='[Is1]-stop_before_start',
        ),
        pytest.param(
            'start_zeroconf_none',
            AttributeError,
            r'zeroconf not configured',
            id='[Is2]-start_when_zeroconf_none',
        ),
        pytest.param(
            'browser_runtime_error',
            RuntimeError,
            r'Maximum number of Zeroconf instances reached\.',
            id='[Is3]-service_browser_runtime_error',
        ),
    ],
)
def test_async_adb_pairing_weak_robust_invalid(
    scenario: str,
    expected_exc: type[Exception],
    match_pattern: str,
    mocker: MockerFixture,
) -> None:
    pairing = AsyncAdbPairing(password='123456')

    async def _run() -> None:
        if scenario == 'stop_before_start':
            await pairing.stop_pair_listener()
        elif scenario == 'start_zeroconf_none':
            mocker.patch.object(pairing, '_new_zeroconf_instance')
            await pairing.start()
        else:
            mocker.patch(
                'device_manager.asyncio_dm.async_adb_pairing.Zeroconf'
            )
            mocker.patch(
                'device_manager.asyncio_dm.async_adb_pairing.AsyncZeroconf'
            )
            mocker.patch(
                'device_manager.asyncio_dm.async_adb_pairing.ServiceBrowser',
                side_effect=RuntimeError('boom'),
            )
            await pairing.start()

    with pytest.raises(expected_exc, match=match_pattern):
        asyncio.run(_run())


def test_async_adb_pairing_context_manager(mocker: MockerFixture) -> None:
    pairing = AsyncAdbPairing(password='123456')
    mock_start = mocker.patch.object(pairing, 'start', new=AsyncMock())
    mock_stop = mocker.patch.object(
        pairing, 'stop_pair_listener', new=AsyncMock()
    )
    mock_pair = mocker.patch.object(
        pairing, 'pair_devices', new=AsyncMock(return_value=False)
    )

    async def _run() -> None:
        async with pairing.pair(max_attempts=2) as qr:
            assert qr == pairing.qrcode_string

    asyncio.run(_run())
    mock_start.assert_awaited_once()
    assert mock_pair.await_count == 2
    mock_stop.assert_awaited_once()
