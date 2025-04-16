import subprocess

import pytest

from device_manager.utils.dm_warnings import (
    ADB_VERSION,
    SDK_VERSION,
    DependencyNotFoundError,
    DependencyVersionError,
    check_adb_dependencies_version,
)


def test_check_adb_dependecies_version(capsys, monkeypatch):
    monkeypatch.setattr(
        'device_manager.utils.dm_warnings.subprocess.run',
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout='Android Debug Bridge version 1.0.41\n'
            'Version 35.0.2-12147458\n'
            'Installed as /usr/bin/adb\n'
            'Revision 0a7d9e12b9b3-android\n',
            stderr='',
        ),
    )

    check_adb_dependencies_version(
        adb_version=ADB_VERSION,
        sdk_version=SDK_VERSION,
    )
    output = capsys.readouterr()

    assert not output.out
    assert not output.err


def test_check_adb_dependencies_version_with_superior_version(
    capsys,
    caplog,
    monkeypatch,
):
    monkeypatch.setattr(
        'device_manager.utils.dm_warnings.subprocess.run',
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout='Android Debug Bridge version 1.3.42\n'
            'Version 36.0.2-12147458\n'
            'Installed as /usr/bin/adb\n'
            'Revision 0a7d9e12b9b3-android\n',
            stderr='',
        ),
    )

    check_adb_dependencies_version(
        adb_version=ADB_VERSION,
        sdk_version=SDK_VERSION,
    )
    output = capsys.readouterr()

    assert not output.out
    assert not output.err
    assert (
        'Your current minor adb version might not work as intended.'
        in caplog.text
    )  # noqa
    assert 'Recommended: 1.0.41' in caplog.text


def test_check_adb_dependencies_version_with_inferior_version(
    capsys,
    caplog,
    monkeypatch,
):
    monkeypatch.setattr(
        'device_manager.utils.dm_warnings.subprocess.run',
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout='Android Debug Bridge version 0.9.41\n'
            'Version 34.0.2-12147458\n'
            'Installed as /usr/bin/adb\n'
            'Revision 0a7d9e12b9b3-android\n',
            stderr='',
        ),
    )

    with pytest.raises(DependencyVersionError) as exc_info:
        check_adb_dependencies_version(
            adb_version=ADB_VERSION,
            sdk_version=SDK_VERSION,
        )

    output = capsys.readouterr()

    assert str(exc_info.value) == 'major adb version is not supported.'
    assert not output.out
    assert not output.err
    assert not caplog.text


def test_check_sdk_dependencies_version_with_inferior_version(
    capsys,
    caplog,
    monkeypatch,
):
    monkeypatch.setattr(
        'device_manager.utils.dm_warnings.subprocess.run',
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout='Android Debug Bridge version 1.3.42\n'
            'Version 28.0.2-12147458\n'
            'Installed as /usr/bin/adb\n'
            'Revision 0a7d9e12b9b3-android\n',
            stderr='',
        ),
    )

    with pytest.raises(DependencyVersionError) as exc_info:
        check_adb_dependencies_version(
            adb_version=ADB_VERSION,
            sdk_version=SDK_VERSION,
        )

    output = capsys.readouterr()

    assert str(exc_info.value) == 'major Android SDK version is not supported.'
    assert not output.out
    assert not output.err
    assert not caplog.text


def test_check_adb_dependecy_not_found(
    capsys,
    caplog,
    monkeypatch,
):
    monkeypatch.setattr(
        'device_manager.utils.dm_warnings.subprocess.run',
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args=args,
            returncode=1,
            stdout='',
            stderr='adb: command not found',
        ),
    )

    with pytest.raises(DependencyNotFoundError) as exc_info:
        check_adb_dependencies_version(
            adb_version=ADB_VERSION,
            sdk_version=SDK_VERSION,
        )

    output = capsys.readouterr()

    assert (
        str(exc_info.value)
        == 'The `android-tools-adb` was not found in your system.'
    )  # noqa
    assert not output.out
    assert not output.err
    assert not caplog.text
