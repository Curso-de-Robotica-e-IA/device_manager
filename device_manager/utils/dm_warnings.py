import logging
import subprocess

from device_manager.exceptions import (
    DependencyNotFoundError,
    DependencyVersionError,
)

logger = logging.getLogger(__name__)

ADB_VERSION = '1.0.41'
SDK_VERSION = '35.0.2'


def check_adb_dependencies_version(
    adb_version: str = ADB_VERSION,
    sdk_version: str = SDK_VERSION,
) -> None:
    try:
        output = (
            subprocess.run(
                args=['adb', 'version'],
                capture_output=True,
                check=True,
                text=True,
            ).stdout
        ).splitlines()

        adb, sdk, *_ = output

        adb_idx = (adb.lower()).find('version')
        sdk_idx = (sdk.lower()).find('version')
        curr_adb_v = (adb[adb_idx + 8 :]).split('.')
        curr_sdk_v = (sdk[sdk_idx + 8 :]).split('.')

        req_adb_v = adb_version.split('.')
        req_sdk_v = sdk_version.split('.')

        for r_adb, c_adb, r_sdk, c_sdk, label in zip(
            req_adb_v,
            curr_adb_v,
            req_sdk_v,
            curr_sdk_v,
            ['major', 'minor'],
        ):
            curr_adb = int(c_adb)
            req_adb = int(r_adb)
            curr_sdk = int(c_sdk)
            req_sdk = int(r_sdk)

            if curr_adb < req_adb:
                raise DependencyVersionError(
                    f'{label} adb version is not supported.',
                )
            elif curr_adb > req_adb:
                msg = (
                    f'Your current {label} adb version might not work as intended.',  # noqa
                    f'Recommended: {adb_version}',
                )
                logger.warning(msg)
            if curr_sdk < req_sdk:
                raise DependencyVersionError(
                    f'{label} Android SDK version is not supported.',
                )
            elif curr_sdk > req_sdk:
                msg = (
                    f'Your current {label} Android SDK version might not work as intended',  # noqa
                    f'Recommended: {sdk_version}',
                )
                logger.warning(msg)
        logger.log(1, 'No problem with the Dependecies Versions.')

    except ValueError:
        raise DependencyNotFoundError(
            'The `android-tools-adb` was not found in your system.'
        )
