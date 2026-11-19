import re

from device_manager.exceptions.errors import UnexpectedAdbOutputError
from device_manager.utils.util_functions import grep

UNEXPECTED_ADB_OUTPUT = 'Unexpected output from ADB command'

ORIENTATION_MAP: dict[str, str] = {
    '0': 'Portrait',
    '1': 'Landscape',
    '2': 'Reverse Portrait',
    '3': 'Reverse Landscape',
}

LOCATION_MODES: dict[str, str] = {
    '0': 'Off',
    '1': 'Sensors Only',
    '2': 'Battery Saving',
    '3': 'High Accuracy',
}


def parse_current_activity(output: str) -> str:
    """Extracts the top resumed activity package/class from dumpsys output."""
    grep_lines = grep(output, 'mCurrentFocus')
    if not grep_lines:
        return 'No activity'
    package_pattern = re.compile(r'com\.[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*')
    result = re.findall(package_pattern, grep_lines[0])
    if not result:
        return 'No activity'
    return '/'.join(result)


def parse_bool_flag(output: str, key: str) -> bool:
    """Parses a single `key=true|false` flag from dumpsys output."""
    grep_lines = grep(output, key)
    if len(grep_lines) != 1:
        raise UnexpectedAdbOutputError(UNEXPECTED_ADB_OUTPUT)
    parts = grep_lines[0].split('=')
    if 'true' in parts:
        return True
    if 'false' in parts:
        return False
    raise UnexpectedAdbOutputError(UNEXPECTED_ADB_OUTPUT)


def parse_getprop(
    output: str,
    extra_keys: list[str] | None = None,
) -> dict[str, str]:
    """Parses `adb shell getprop` output into a normalized dictionary."""
    prop_dict: dict[str, str] = {}
    expected_length = 2
    for line in output.splitlines():
        key_value = line.split(': ', 1)
        if len(key_value) == expected_length:
            prop_dict[key_value[0][1:-1]] = key_value[1][1:-1]

    base_result: dict[str, str] = {
        'serial_number': prop_dict['ro.serialno'],
        'brand': prop_dict['ro.product.manufacturer'],
        'model': prop_dict['ro.product.model'],
        'android_version': prop_dict['ro.build.version.release'],
    }
    if extra_keys is not None:
        for key in extra_keys:
            if key in prop_dict:
                base_result[key] = prop_dict[key]
    return base_result


def parse_screen_dimensions(output: str) -> tuple[int, int]:
    """Parses `wm size` output into a (width, height) tuple."""
    grep_lines = grep(output, 'Physical size:')
    if grep_lines:
        dimensions = grep_lines[0].split(':')[1].strip().split('x')
        return int(dimensions[0]), int(dimensions[1])
    raise UnexpectedAdbOutputError(UNEXPECTED_ADB_OUTPUT)


def parse_display_orientation(output: str) -> str:
    """Parses `dumpsys display` output into a human-readable orientation."""
    grep_lines = grep(output, 'mCurrentOrientation')
    if grep_lines:
        orientation_value = grep_lines[0].split('=')[1].strip()
        return ORIENTATION_MAP.get(orientation_value, 'Unknown')
    raise UnexpectedAdbOutputError(UNEXPECTED_ADB_OUTPUT)


def parse_installed_packages(output: str) -> list[str]:
    """Parses `pm list packages` output into a list of package names."""
    return [
        line.replace('package:', '').strip()
        for line in output.splitlines()
        if line.strip().startswith('package:')
    ]


def parse_app_path(output: str) -> str | None:
    """Parses `pm path <pkg>` output into the APK path on device."""
    for line in output.splitlines():
        if line.strip().startswith('package:'):
            return line.replace('package:', '').strip()
    return None


def parse_location_mode(output: str) -> str | None:
    """Maps `settings get secure location_mode` numeric output to label."""
    return LOCATION_MODES.get(output.strip(), None)
