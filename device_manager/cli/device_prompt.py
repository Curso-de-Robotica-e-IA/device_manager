from rich.console import Console
from rich.prompt import Prompt

from device_manager.connection.connection_manager import ConnectionManager


class DevicePromptCLI:
    """Dedicated CLI presenter handling interactive Rich prompts for pairing
    and selecting devices, decoupled from core connection domain logic (SRP).
    """

    def __init__(
        self,
        connection_manager: ConnectionManager,
        console: Console | None = None,
    ) -> None:
        self.connection = connection_manager
        self.console = console or Console()

    def check_pairing(self) -> None:
        prompt = Prompt()
        response = prompt.ask(
            'Device already paired with host?',
            choices=['Y', 'N'],
            case_sensitive=False,
        )
        paired = response.upper() != 'N'

        if not paired:
            self.console.print('Scan QRCode to pair and close window')
            if self.connection.device_pairing(5):
                self.console.print('Success in pairing new host!')
            else:
                self.console.print('Failed in pairing new host!')

    def select_devices_to_connect(self) -> list[str]:
        prompt = Prompt()
        finish_loop = False
        available_devices = self.connection.available_devices()
        selected_devices: list[str] = []
        while not finish_loop:
            prompt_options = {
                str(i + 1): f'{srnmb} on IP: {available_devices[srnmb].ip}'
                for i, srnmb in enumerate(available_devices)
            }
            self.console.print('Available devices found in the network:')
            for key, prompt_msg in prompt_options.items():
                self.console.print(f'  [{key}] - {prompt_msg}')
            options = list(prompt_options.keys())
            options.append('0')
            response = prompt.ask(
                'Select device index to connect, or 0 to search devices again',
                choices=options,
            )

            if response == '0':
                available_devices = self.connection.available_devices()
            else:
                device_idx = int(response) - 1
                device = list(available_devices.keys())[device_idx]
                selected_devices.append(device)

                connect_another = prompt.ask(
                    'Do you want to connect to another device?',
                    choices=['Y', 'N'],
                    case_sensitive=False,
                )
                if connect_another.upper() == 'N':
                    finish_loop = True

        return selected_devices

    def prompt_device_connection(self) -> list[str]:
        prompt = Prompt()
        done = False
        while not done:
            self.check_pairing()
            res = prompt.ask(
                'Do you want to pair another device?',
                choices=['Y', 'N'],
                case_sensitive=False,
            )
            done = res.upper() == 'N'
        return self.select_devices_to_connect()
