from enum import Enum


class AdbStreamCommand(Enum):
    """Supported ADB shell streaming commands for `DeviceActions.start_stream`."""

    GETEVENT = 'getevent -lt'
    LOGCAT = 'logcat'
    DMESG = 'dmesg -w'
    TOP = 'top -b'
    SCREENRECORD = 'screenrecord --output-format=h264 -'
    CUSTOM = ''
