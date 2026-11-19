import subprocess
from subprocess import CompletedProcess
from typing import Any, Callable, Protocol, Sequence


class AdbGateway(Protocol):
    """Adapter interface for executing ADB commands."""

    def run(
        self,
        args: Sequence[str],
        *,
        check: bool = False,
        capture_output: bool = False,
        text: bool | None = None,
    ) -> CompletedProcess[Any]: ...


class SubprocessAdbGateway:
    """Default AdbGateway implementation backed by subprocess.run."""

    def __init__(
        self,
        runner: Callable[..., CompletedProcess[Any]] | None = None,
    ) -> None:
        self._runner = runner

    def run(
        self,
        args: Sequence[str],
        *,
        check: bool = False,
        capture_output: bool = False,
        text: bool | None = None,
    ) -> CompletedProcess[Any]:
        runner = self._runner or subprocess.run
        return runner(
            list(args),
            shell=False,
            check=check,
            capture_output=capture_output,
            text=text,
        )


def resolve_gateway(
    gateway: AdbGateway | None,
    runner: Callable[..., CompletedProcess[Any]] = subprocess.run,
) -> AdbGateway:
    """Return the injected gateway or wrap `runner` in SubprocessAdbGateway."""
    return gateway if gateway is not None else SubprocessAdbGateway(runner=runner)
