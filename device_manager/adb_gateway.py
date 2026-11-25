import subprocess
from subprocess import CompletedProcess
from typing import Any, Callable, Protocol, Sequence

from device_manager.adb_stream import AdbStreamProcess


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


class AdbutilsAdbGateway:
    """High-performance AdbGateway backed by persistent `adbutils` TCP sockets.

    Avoids spawning `adb.exe` subprocesses for `devices`, `shell`, `push`,
    `pull`, and `exec-out`, falling back to `SubprocessAdbGateway` for
    unsupported commands (e.g., `pair`, `start-server`, `kill-server`).
    """

    def __init__(
        self,
        client: Any | None = None,
        fallback: AdbGateway | None = None,
    ) -> None:
        self._client = client
        self._fallback = fallback or SubprocessAdbGateway()

    def _get_client(self) -> Any:
        if self._client is None:
            import adbutils  # noqa: PLC0415

            self._client = adbutils.adb
        return self._client

    def open_stream(
        self,
        serial: str,
        command: str,
        *,
        timeout: float | None = None,
        encoding: str | None = 'utf-8',
    ) -> AdbStreamProcess:
        """Open a persistent streaming ADB shell session via `adbutils`."""
        device = self._get_client().device(serial=serial)
        conn = device.shell(command, stream=True, timeout=timeout)
        return AdbStreamProcess(conn, command=command, encoding=encoding)

    def run(
        self,
        args: Sequence[str],
        *,
        check: bool = False,
        capture_output: bool = False,
        text: bool | None = None,
    ) -> CompletedProcess[Any]:
        cmd = list(args)
        if not cmd or cmd[0] != 'adb':
            return self._fallback.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=text,
            )

        try:
            client = self._get_client()

            # adb devices
            if cmd == ['adb', 'devices']:
                lines = ['List of devices attached']
                for info in client.list():
                    lines.append(f'{info.serial}\t{info.state}')
                stdout = '\n'.join(lines) + '\n'
                return CompletedProcess(
                    args=cmd,
                    returncode=0,
                    stdout=stdout if text is not False else stdout.encode(),
                    stderr='' if text is not False else b'',
                )

            # adb -s <serial> <subcmd> ...
            if len(cmd) >= 4 and cmd[1] == '-s':
                serial = cmd[2]
                subcmd = cmd[3]
                rest = cmd[4:]
                device = client.device(serial=serial)

                if subcmd == 'shell' and rest:
                    out = device.shell(rest)
                    return CompletedProcess(
                        args=cmd, returncode=0, stdout=out, stderr=''
                    )

                if subcmd == 'exec-out' and rest:
                    raw = device.shell(rest, encoding=None)
                    return CompletedProcess(
                        args=cmd, returncode=0, stdout=raw, stderr=b''
                    )

                if subcmd == 'push' and len(rest) == 2:
                    device.sync.push(rest[0], rest[1])
                    return CompletedProcess(
                        args=cmd, returncode=0, stdout='', stderr=''
                    )

                if subcmd == 'pull' and len(rest) == 2:
                    device.sync.pull(rest[0], rest[1])
                    return CompletedProcess(
                        args=cmd, returncode=0, stdout='', stderr=''
                    )
        except Exception as exc:
            if check:
                raise subprocess.CalledProcessError(
                    returncode=1, cmd=cmd, output='', stderr=str(exc)
                ) from exc
            return CompletedProcess(
                args=cmd,
                returncode=1,
                stdout='' if text is not False else b'',
                stderr=str(exc) if text is not False else str(exc).encode(),
            )

        return self._fallback.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=text,
        )


def resolve_gateway(
    gateway: AdbGateway | None,
    runner: Callable[..., CompletedProcess[Any]] = subprocess.run,
) -> AdbGateway:
    """Return the injected gateway or wrap `runner` in SubprocessAdbGateway."""
    return (
        gateway if gateway is not None else SubprocessAdbGateway(runner=runner)
    )
