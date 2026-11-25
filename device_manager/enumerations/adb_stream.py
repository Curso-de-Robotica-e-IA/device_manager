from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


@runtime_checkable
class AdbStreamSpec(Protocol):
    """Polymorphic contract for any ADB shell streaming specification."""

    def build_command(self) -> str:
        """Return the full ADB shell command string to stream."""
        ...

    @property
    def default_encoding(self) -> str | None:
        """Default text encoding (`None` for binary streams)."""
        ...


@dataclass(frozen=True)
class CustomAdbStream:
    """Custom ADB shell stream specification implementing `AdbStreamSpec`."""

    command: str
    encoding: str | None = 'utf-8'

    def __post_init__(self) -> None:
        if not self.command or not self.command.strip():
            raise ValueError('CustomAdbStream requires a non-empty command.')

    def build_command(self) -> str:
        return self.command.strip()

    @property
    def default_encoding(self) -> str | None:
        return self.encoding


class AdbStreamCommand(Enum):
    """Built-in ADB shell stream presets implementing `AdbStreamSpec`."""

    GETEVENT = ('getevent -lt', 'utf-8')
    LOGCAT = ('logcat', 'utf-8')
    DMESG = ('dmesg -w', 'utf-8')
    TOP = ('top -b', 'utf-8')
    SCREENRECORD = ('screenrecord --output-format=h264 -', None)

    def __init__(self, command: str, encoding: str | None) -> None:
        self._command = command
        self._encoding = encoding

    def build_command(self) -> str:
        """Return the preset ADB shell command."""
        return self._command

    @property
    def default_encoding(self) -> str | None:
        """Return the default encoding for this preset (`None` for binary)."""
        return self._encoding

    def with_args(self, *args: str) -> CustomAdbStream:
        """Return a new stream spec appending extra CLI arguments to this preset."""
        extra = ' '.join(arg.strip() for arg in args if arg.strip())
        full_cmd = f'{self._command} {extra}'.strip()
        return CustomAdbStream(command=full_cmd, encoding=self._encoding)
