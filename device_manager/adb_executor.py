import shlex
import subprocess
from subprocess import CompletedProcess

from device_manager.adb_gateway import AdbGateway, resolve_gateway


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
        last_result = active_gateway.run(
            cmd_args,
            check=subprocess_check_flag,
            capture_output=capture_output,
            text=capture_output if capture_output else None,
        )
    assert last_result is not None
    return last_result
