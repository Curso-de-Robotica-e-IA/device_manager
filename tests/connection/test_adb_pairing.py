from unittest.mock import MagicMock

import pytest

from device_manager.connection.adb_pairing import AdbPairing


@pytest.fixture
def sample_service(mocker):
    """Provides a mock ServiceInfo object with predefined network data."""
    service = mocker.MagicMock()
    service.ip = '192.168.155.87'
    service.port = 5555
    return service


@pytest.fixture
def mock_zeroconf_adb_pairing(mocker):
    """Patches Zeroconf class to prevent real network socket creation."""
    mock_class = mocker.patch('device_manager.connection.adb_pairing.Zeroconf')
    instance = mock_class.return_value
    instance.service_info = mocker.MagicMock()
    instance.service_info.addresses = [b'\x7f\x00\x00\x01']
    instance.service_info.port = 5555
    instance.service_info.name = (
        'adb-emulator-5555._adb-tls-connect._tcp.local.'
    )
    instance.service_info.server = 'test-server'
    instance.get_service_info.return_value = instance.service_info
    return instance


@pytest.fixture
def adb_pairing(mock_zeroconf_adb_pairing):
    """Provides a fresh AdbPairing instance for each test."""
    return AdbPairing()


def test_init_with_explicit_password(mock_zeroconf_adb_pairing):
    """Ensure the class accepts and stores a manually provided password."""
    custom_pass = 'my_secret_pass'
    pairing = AdbPairing(password=custom_pass)
    assert pairing.password == custom_pass


def test_initial_properties_state(adb_pairing):
    """Verify that properties return correct default values before any action."""
    assert adb_pairing.browser is None
    assert adb_pairing.password == adb_pairing._passwd
    assert adb_pairing.zeroconf_status is False
    assert adb_pairing.qrcode is not None
    assert adb_pairing.qrcode_image is not None


def test_zeroconf_status_alive(adb_pairing, mocker):
    """Covers line 144 by checking the alive status of the finalize object."""
    mocker.patch('device_manager.connection.adb_pairing.ServiceBrowser')
    mock_fin = mocker.patch('device_manager.connection.adb_pairing.finalize')
    mock_fin.return_value.alive = True

    adb_pairing.start()
    assert adb_pairing.zeroconf_status is True


def test_update_qrcode_persistence(adb_pairing, mocker):
    """Verify that update_qrcode preserves the existing password when requested."""
    mock_qr = mocker.patch('device_manager.connection.adb_pairing.QRCode')
    current_password = adb_pairing._passwd
    adb_pairing.update_qrcode(new_password=False)
    assert adb_pairing._passwd == current_password
    assert mock_qr.call_count == 1


def test_update_qrcode_rotation(adb_pairing, mocker):
    """Verify that update_qrcode generates a new password when requested."""
    mocker.patch('device_manager.connection.adb_pairing.QRCode')
    mocker.patch(
        'device_manager.connection.adb_pairing.create_password',
        return_value='999999',
    )
    old_password = adb_pairing._passwd
    adb_pairing.update_qrcode(new_password=True)
    assert adb_pairing._passwd == '999999'
    assert adb_pairing._passwd != old_password


def test_set_password_behavior(adb_pairing, mocker):
    """Test explicit password setting with and without QR code update."""
    mock_update = mocker.patch.object(adb_pairing, 'update_qrcode')
    new_pass = '123456'

    adb_pairing.set_password(new_pass, update_qrcode=True)
    assert adb_pairing._passwd == new_pass
    mock_update.assert_called_with(new_password=False)

    mock_update.reset_mock()
    adb_pairing.set_password('999999', update_qrcode=False)
    mock_update.assert_not_called()


def test_start_engine_configuration(
    adb_pairing, mocker, mock_zeroconf_adb_pairing
):
    """Verify that start() initializes MDnsListener and ServiceBrowser correctly."""
    mock_browser = mocker.patch(
        'device_manager.connection.adb_pairing.ServiceBrowser'
    )
    mock_listener = mocker.patch(
        'device_manager.connection.adb_pairing.MDnsListener'
    )
    mocker.patch('device_manager.connection.adb_pairing.finalize')

    adb_pairing.start(unicast=True)
    mock_listener.assert_called_once()
    mock_browser.assert_called_once()
    assert adb_pairing.service_browser_started is True


def test_start_prevents_duplicate_browsers(adb_pairing, mocker):
    """Ensure start() does not create multiple browsers if already running."""
    mock_browser = mocker.patch(
        'device_manager.connection.adb_pairing.ServiceBrowser'
    )
    mocker.patch('device_manager.connection.adb_pairing.finalize')
    adb_pairing.start()
    adb_pairing.start()
    assert mock_browser.call_count == 1


def test_start_runtime_error_wrapping(adb_pairing, mocker):
    """Verify that Zeroconf instance limits trigger a custom RuntimeError."""
    mocker.patch(
        'device_manager.connection.adb_pairing.ServiceBrowser',
        side_effect=RuntimeError,
    )
    mocker.patch('device_manager.connection.adb_pairing.Zeroconf')
    with pytest.raises(
        RuntimeError, match='Maximum number of Zeroconf instances reached.'
    ):
        adb_pairing.start()


def test_stop_cleans_resources(adb_pairing, mocker, mock_zeroconf_adb_pairing):
    """Verify that stop_pair_listener closes Zeroconf and resets internal state."""
    mocker.patch('device_manager.connection.adb_pairing.ServiceBrowser')
    mocker.patch('device_manager.connection.adb_pairing.finalize')
    adb_pairing.start()
    adb_pairing.stop_pair_listener()
    mock_zeroconf_adb_pairing.close.assert_called_once()
    assert adb_pairing.browser is None
    assert adb_pairing.service_browser_started is False


def test_finalize_atexit_cleanup(adb_pairing, mocker):
    """Verify the internal callback logic used during object finalization."""
    mocker.patch('device_manager.connection.adb_pairing.ServiceBrowser')
    mock_fin = mocker.patch('device_manager.connection.adb_pairing.finalize')
    adb_pairing.start()
    callback = mock_fin.call_args[0][1]
    callback()
    assert adb_pairing.browser is None
    assert adb_pairing.service_browser_started is False


def test_new_zeroconf_instance_zombies(adb_pairing, mocker):
    """Covers lines 237-238 by testing the logic that moves old Zeroconf instances to zombies."""
    mocker.patch('device_manager.connection.adb_pairing.Zeroconf')
    adb_pairing._new_zeroconf_instance()
    initial_zc = adb_pairing._zeroconf

    adb_pairing._new_zeroconf_instance()
    assert len(adb_pairing._zeroconf_zombies) == 1
    assert adb_pairing._zeroconf_zombies[0] == initial_zc


def test_device_discovery_status(adb_pairing, mocker, sample_service):
    """Verify has_device_to_pairing correctly checks the online context."""
    mocker.patch.object(
        adb_pairing._context, 'get_online_service', return_value={}
    )
    assert adb_pairing.has_device_to_pairing() is False

    mocker.patch.object(
        adb_pairing._context,
        'get_online_service',
        return_value={'dev': sample_service},
    )
    assert adb_pairing.has_device_to_pairing() is True


def test_pair_devices_adb_success(adb_pairing, sample_service, mocker):
    """Verify success return when ADB pairing command output is valid."""
    mocker.patch.object(
        adb_pairing._context,
        'get_online_service',
        return_value={'dev': sample_service},
    )
    mock_res = mocker.MagicMock(
        stdout=f'Successfully paired to {sample_service.ip}:{sample_service.port}'
    )
    mocker.patch(
        'device_manager.connection.adb_pairing.subprocess.run',
        return_value=mock_res,
    )
    assert adb_pairing.pair_devices() is True


def test_pair_devices_adb_failure(adb_pairing, sample_service, mocker):
    """Verify False return when ADB pairing command fails."""
    mocker.patch.object(
        adb_pairing._context,
        'get_online_service',
        return_value={'dev': sample_service},
    )
    mock_res = mocker.MagicMock(stdout='Failed: error')
    mocker.patch(
        'device_manager.connection.adb_pairing.subprocess.run',
        return_value=mock_res,
    )
    assert adb_pairing.pair_devices() is False


def test_pair_devices_no_online_services(adb_pairing, mocker):
    """Covers line 341 by ensuring it returns False when the service list is empty."""
    mocker.patch.object(
        adb_pairing._context, 'get_online_service', return_value={}
    )
    assert adb_pairing.pair_devices() is False


def test_context_manager_lifecycle(adb_pairing, mocker):
    mock_start = mocker.patch.object(adb_pairing, 'start')
    mock_stop = mocker.patch.object(adb_pairing, 'stop_pair_listener')
    mock_pair = mocker.patch.object(
        adb_pairing, 'pair_devices', return_value=True
    )

    with adb_pairing.pair() as qr:
        assert qr == adb_pairing.qrcode_string
        mock_start.assert_called_once()

    mock_pair.assert_called_once()
    mock_stop.assert_called_once()


def test_context_manager_retry_limit(adb_pairing, mocker):
    """Verify that the context manager respects the max_attempts on failure."""
    mocker.patch.object(adb_pairing, 'start')
    mocker.patch.object(adb_pairing, 'stop_pair_listener')
    mock_pair = mocker.patch.object(
        adb_pairing, 'pair_devices', return_value=False
    )

    with adb_pairing.pair(max_attempts=3) as _:
        pass

    assert mock_pair.call_count == 3
