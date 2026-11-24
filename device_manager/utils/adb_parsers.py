import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from device_manager.exceptions.errors import UnexpectedAdbOutputError
from device_manager.utils.util_functions import grep


@dataclass(frozen=True)
class TouchscreenInfo:
    """Metadata and axis ranges for an Android `/dev/input/event*` touchscreen."""

    node: str
    name: str
    x_range: tuple[int, int]
    y_range: tuple[int, int]


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


_BOUNDS_RE = re.compile(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]')


def find_text_bounds_center(
    xml_content: str,
    text: str,
    *,
    exact: bool = False,
) -> tuple[int, int] | None:
    """Finds the center `(x, y)` of the first UI node matching `text` or `content-desc`."""
    if not xml_content or not text:
        return None
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return None

    target = text if exact else text.lower()
    for node in root.iter():
        for attr in ('text', 'content-desc'):
            val = node.attrib.get(attr, '')
            if not val:
                continue
            matched = val == target if exact else target in val.lower()
            if matched:
                bounds = node.attrib.get('bounds', '')
                m = _BOUNDS_RE.search(bounds)
                if m:
                    x1, y1, x2, y2 = (int(g) for g in m.groups())
                    return (x1 + x2) // 2, (y1 + y2) // 2
    return None


_AXIS_MIN_RE = re.compile(r'\bmin\s+(\d+)')
_AXIS_MAX_RE = re.compile(r'\bmax\s+(\d+)')


def _parse_axis_bounds(line: str) -> tuple[int, int] | None:
    m_min = _AXIS_MIN_RE.search(line)
    m_max = _AXIS_MAX_RE.search(line)
    if m_min and m_max:
        return int(m_min.group(1)), int(m_max.group(1))
    return None


def parse_touchscreen_devices(
    output: str,
) -> tuple[dict[str, TouchscreenInfo], list[str]]:
    """Parses `getevent -p -l` output into `(touchscreens_by_node, prioritized_nodes)`.

    Direct touch devices (`INPUT_PROP_DIRECT`) are ordered before indirect ones.
    """
    devices: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith('add device'):
            if current is not None:
                devices.append(current)
            node = (
                line.split('/dev/input/')[-1].strip()
                if '/dev/input/' in line
                else ''
            )
            current = {
                'node': node,
                'name': '',
                'is_direct': False,
                'has_touch_axis': False,
                'x_range': None,
                'y_range': None,
            }
        elif current is not None:
            if line.startswith('name:'):
                current['name'] = line.split('name:', 1)[-1].strip().strip('"')
            elif 'INPUT_PROP_DIRECT' in line:
                current['is_direct'] = True
            elif 'ABS_MT_POSITION_X' in line or (
                'ABS_X' in line and current['x_range'] is None
            ):
                current['has_touch_axis'] = True
                bounds = _parse_axis_bounds(line)
                if bounds is not None:
                    current['x_range'] = bounds
            elif 'ABS_MT_POSITION_Y' in line or (
                'ABS_Y' in line and current['y_range'] is None
            ):
                current['has_touch_axis'] = True
                bounds = _parse_axis_bounds(line)
                if bounds is not None:
                    current['y_range'] = bounds

    if current is not None:
        devices.append(current)

    touch_map: dict[str, TouchscreenInfo] = {}
    direct_nodes: list[str] = []
    indirect_nodes: list[str] = []

    for dev in devices:
        node = str(dev['node'])
        if not node or not dev['has_touch_axis']:
            continue
        x_range = dev['x_range'] or (0, 0)
        y_range = dev['y_range'] or (0, 0)
        touch_map[node] = TouchscreenInfo(
            node=node,
            name=str(dev['name']),
            x_range=x_range,  # type: ignore[arg-type]
            y_range=y_range,  # type: ignore[arg-type]
        )
        if dev['is_direct']:
            direct_nodes.append(node)
        else:
            indirect_nodes.append(node)

    return touch_map, direct_nodes + indirect_nodes
