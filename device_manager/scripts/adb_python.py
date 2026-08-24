import subprocess, shlex


class ManagerDevice:
    def __init__(self, serial_number="N3KN4M0112", port=""):
        self.serial_number = serial_number
        self.ip = f'192.168.158.10:{port}'

    def append_port_ip(self):
        if len(self.ip) < 15:
            self.ip_port = f'{self.ip_port}:{input('input port -> ')}'

    def execute_adb_pair_ip(self):
        subprocess.run(['adb', 'pair', self.serial_number])
        
    def execute_adb_connect_port(self):
        subprocess.run(['adb', 'connect', self.serial_number])
        
    def execute_turn_on_turn_off_display(self):
        subprocess.run(['adb','-s',f'{self.serial_number}', 'shell' , 'input', 'keyevent', '26' ])

    def get_information_device(self):
        subprocess.run(['adb', 'devices', '-l'])

    def size_display(self):
        subprocess.run(['adb', '-s', f'{self.serial_number}', 'shell','wm', 'size'])

    def list_all_apps(self):
        subprocess.run(['adb', '-s', f'{self.serial_number}', 'shell','list', 'packages', '-u'])

    def go_to_home(self):
        subprocess.run(['adb','-s',f'{self.serial_number}', 'shell' , 'input', 'keyevent', '3'])


def execute_adb_devices():
    subprocess.run(['adb', 'devices'])

if __name__ == "__main__":
    subprocess.run(['adb','-s','N3KN4M0112', 'shell' , 'am', 'start', '-a'])
