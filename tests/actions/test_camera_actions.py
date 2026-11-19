from pathlib import Path
import subprocess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from device_manager.actions.camera_actions import CameraActions


@pytest.fixture
def camera_actions() -> CameraActions:
    conn = MagicMock()
    conn.build_comm_uri.return_value = '192.168.1.10:5555'
    return CameraActions(
        device_connection=conn,
        serial_number='SER123',
        subprocess_check_flag=False,
        comm_uri='192.168.1.10:5555',
        validate_connection_callback=lambda: True,
    )


def test_camera_actions_basic_commands(
    camera_actions: CameraActions,
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    mock_exec = mocker.patch(
        'device_manager.base_device_component.execute_adb_command',
        return_value=subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout='com.android.camera/com.android.camera.Camera\n',
        ),
    )

    camera_actions.open()
    camera_actions.open_video()
    camera_actions.close()
    assert camera_actions.package() == 'com.android.camera'
    camera_actions.take_picture()
    camera_actions.clear_pictures()

    with pytest.raises(ValueError, match='Source path invalid'):
        camera_actions.clear_pictures(None)

    mock_exec.return_value = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout='1 file pulled, 0 skipped.\n',
    )
    camera_actions.pull_picture_by_name('img.jpg', tmp_path)


def test_camera_actions_raises_when_disconnected() -> None:
    conn = MagicMock()
    conn.build_comm_uri.side_effect = ValueError('not found')
    cam = CameraActions(
        device_connection=conn,
        serial_number='SER123',
        subprocess_check_flag=False,
        comm_uri='fallback:5555',
        validate_connection_callback=lambda: False,
    )
    assert cam.current_comm_uri == 'fallback:5555'
    with pytest.raises(RuntimeError):
        cam.open()
    with pytest.raises(RuntimeError):
        cam.open_video()
    with pytest.raises(RuntimeError):
        cam.close()
    with pytest.raises(RuntimeError):
        cam.package()
    with pytest.raises(RuntimeError):
        cam.take_picture()
    with pytest.raises(RuntimeError):
        cam.clear_pictures()
