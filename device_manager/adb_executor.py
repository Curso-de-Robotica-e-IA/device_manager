import subprocess
from subprocess import CompletedProcess
from typing import List


def build_command_list(
    base_command: List[str],
    comm_uri_list: List[str],
    custom_command: str,
    **kwargs,
) -> List[str]:
    """Builds a list of commands to be executed on multiple devices.
    This method is used to build a list of commands that will be executed
    on multiple devices. The command is built using the base command
    provided, the list of communication URIs, the custom command to be
    executed, and any additional arguments that should be added to the
    command.

    Args:
        base_command (List[str]): The base command to be executed.
        comm_uri_list (List[str]): The list of communication URIs for the
            devices.
        custom_command (str): The custom command to be executed.
        **kwargs: Additional arguments to be added to the command.
    """
    command = base_command.copy()
    command_as_list = custom_command.split(' ')
    for idx, uri in enumerate(comm_uri_list):
        command.extend(['-s', uri])
        command.extend(command_as_list)
        if idx < len(comm_uri_list) - 1:
            command.extend(['&&', 'adb'])
    if kwargs:
        for key, value in kwargs.items():
            command.extend([key, value])
    return command


def execute_adb_command(
    command: str,
    comm_uris: List[str],
    shell: bool = False,
    subprocess_check_flag: bool = False,
    capture_output: bool = False,
    **kwargs,
) -> CompletedProcess:
    """Executes a custom adb command on all connected devices.
    Additional arguments and keyword arguments can be provided to
    customize the command, which will be added to the end of the command
    string.

    Passing a command such as `pull remote local` will produce the
    following command: `adb pull remote local`, applied with the
    `-s` flag for each device.

    You can execute a command on a set of specific devices by providing
    the serial numbers as additional arguments.

    Args:
        command (str): The adb command to execute.
        comm_uris (List[str]): The serial numbers of the
            devices to execute the command on.
        shell (bool, optional): A flag to indicate if the command should
            be executed as adb shell. Defaults to False.
        subprocess_check_flag (bool, optional): A flag to check if the
            subprocess execution was successful, passed to the subprocess
            `check` argument. Defaults to False.
            Check the subprocess documentation for more information.
        capture_output (bool, optional): A flag to capture the output of
            the command. Defaults to False.
        **kwargs: Additional arguments to be added to the command.

    Returns:
        CompletedProcess: The result of the command execution.
    """
    if not comm_uris:
        raise ValueError('No devices specified for command execution.')
    base_command = ['adb']
    if command.startswith('adb'):
        command = command[3:]
    if shell:
        if not command.startswith('shell'):
            command = f'shell {command}'
    adb_command_list = build_command_list(
        base_command=base_command,
        comm_uri_list=comm_uris,
        custom_command=command,
        **kwargs,
    )
    adb_command = ' '.join(adb_command_list)
    return subprocess.run(
        adb_command,
        shell=True,
        check=subprocess_check_flag,
        capture_output=capture_output,
        text=capture_output if capture_output else None,
    )
