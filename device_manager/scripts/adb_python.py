import subprocess, shlex

class ManagerDevice:
    def __init__(self, serial_number="", port=""):
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

    def open_camera_with_activity(self):
        subprocess.run(['adb', '-s', f'{self.serial_number}', 'shell', 'am', 'start', '-n', 'com.android.camera2/com.android.camera.CameraLauncher'])

    def get_camera_with_activity(self):
        command = "adb shell dumpsys window | findstr mCurrentFocus"
        result = subprocess.run(command, shell=True,capture_output=True, text=True)
        print(result.stdout)

    def is_stay_awake(self):
        command_get = "adb shell settings get global stay_on_while_plugged_in"
        result = subprocess.run(command_get, shell=True,capture_output=True, text=True)
        if int(result.stdout) > 0 and result.stdout.strip().isdigit():
            command_put = "adb shell settings put global stay_on_while_plugged_in 0"
            subprocess.run(command_put, shell=True,capture_output=True, text=True)

                        


def execute_adb_devices():
    subprocess.run(['adb', 'devices'])

if __name__ == "__main__":
    devices = ManagerDevice('')
    











