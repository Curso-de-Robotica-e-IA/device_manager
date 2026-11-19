import logging
import shlex
import subprocess
from subprocess import CompletedProcess
from time import perf_counter

from device_manager.adb_gateway import AdbGateway, resolve_gateway

logger = logging.getLogger(__name__)


def execute_adb_command(
    command: str,
    comm_uris: list[str],
    shell: bool = False,
    subprocess_check_flag: bool = False,
    capture_output: bool = False,
    gateway: AdbGateway | None = None,
    **kwargs: str,
) -> CompletedProcess[str]:
    """Executes a custom adb command on the specified devices."""
    if not comm_uris:
        raise ValueError('No devices specified for command execution.')
    tokens = shlex.split(command)
    if tokens and tokens[0] == 'adb':
        tokens = tokens[1:]
    if shell and (not tokens or tokens[0] != 'shell'):
        tokens = ['shell', *tokens]

    extra_args: list[str] = []
    for key, value in kwargs.items():
        extra_args.extend([key, value])

    active_gateway = resolve_gateway(gateway, subprocess.run)
    last_result: CompletedProcess[str] | None = None
    for uri in comm_uris:
        cmd_args = ['adb', '-s', uri, *tokens, *extra_args]
        started_at = perf_counter()
        last_result = active_gateway.run(
            cmd_args,
            check=subprocess_check_flag,
            capture_output=capture_output,
            text=capture_output if capture_output else None,
        )
        duration_ms = (perf_counter() - started_at) * 1000
        if last_result.returncode != 0:
            stderr_preview = (last_result.stderr or '').strip() if capture_output else ''
            logger.warning(
                'ADB command failed: uri=%s command=%s returncode=%d duration_ms=%.1f stderr=%s',
                uri,
                command,
                last_result.returncode,
                duration_ms,
                stderr_preview,
            )
        else:
            logger.debug(
                'ADB command succeeded: uri=%s command=%s returncode=%d duration_ms=%.1f',
                uri,
                command,
                last_result.returncode,
                duration_ms,
            )
    assert last_result is not None
    return last_result
