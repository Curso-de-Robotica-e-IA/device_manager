import logging
import subprocess

from device_manager.exceptions import (
    DependencyNotFoundError,
    DependencyVersionError,
)

logger = logging.getLogger(__name__)

ADB_VERSION = '1.0.41'
SDK_VERSION = '35.0.2'


def _check_version_part(
    component: str,
    level: str,
    curr_part: int,
    req_part: int,
    recommended: str,
) -> None:
    if curr_part < req_part:
        raise DependencyVersionError(
            f'{level} {component} version is not supported.',
        )
    if curr_part > req_part:
        logger.warning(
            'Your current %s %s version might not work as intended. '
            'Recommended: %s',
            level,
            component,
            recommended,
        )


def check_adb_dependencies_version(
    adb_version: str = ADB_VERSION,
    sdk_version: str = SDK_VERSION,
) -> None:
    try:
        output = subprocess.run(
            args=['adb', 'version'],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.splitlines()

        adb_line, sdk_line, *_ = output
        curr_adb = adb_line.lower().split('version', 1)[1].strip().split('.')
        curr_sdk = sdk_line.lower().split('version', 1)[1].strip().split('.')
        req_adb = adb_version.split('.')
        req_sdk = sdk_version.split('.')

        for idx, level in enumerate(('major', 'minor')):
            _check_version_part(
                'adb', level, int(curr_adb[idx]), int(req_adb[idx]), adb_version,
            )
            _check_version_part(
                'Android SDK',
                level,
                int(curr_sdk[idx]),
                int(req_sdk[idx]),
                sdk_version,
            )
        logger.log(1, 'No problem with the Dependecies Versions.')

    except (ValueError, FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise DependencyNotFoundError(
            'The `android-tools-adb` was not found in your system.',
        ) from exc
