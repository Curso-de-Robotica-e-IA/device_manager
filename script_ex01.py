import subprocess
from time import sleep

class DeviceManager:
    def __init__(self, ip=None):
        self.ip = ip

    def _show_devices(self):
        process = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True
        ).stdout
        devices = [device.split('\t') for device in process.strip('\n').split('\n')[1:]]
        devices_usb = []
        devices_wifi = []
        for i in devices:
            if i[0].isalnum():
                devices_usb.append(i)
            else:
                devices_wifi.append(i)
        return f'Dispositivos no USB {devices_usb}\nDispositivos no Wifi {devices_wifi}'
    
    def devices_list(self):
        return subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True
        ).stdout
        
    def connect_device(self):
        device_ip = input("Digite o IP e a porta do seu dispositivo, abaixo de Nome do dispositivo <ip:port> : ")
        self.ip = device_ip
        process = subprocess.run(
            ["adb", "connect", device_ip],
            capture_output=True,
            text=True
        )
        return process.stdout
    
    def pair_device(self, ip, code):
        process = subprocess.run(
                ["adb", "pair", ip, code],
                capture_output=True,
                text=True
            )
        
        print(self._show_devices())

    def is_screen_on(self):
        process = subprocess.run(
            ["adb", "-s", self.ip, "shell", "dumpsys deviceidle | grep mScreenOn"],
            capture_output=True,
            text=True
        )

        print(process.stdout.strip().split("="))
        _, status = process.stdout.strip().split("=")
        
        if status == 'true':
            print('A tela está ligada!')
        elif status == 'false':
            print('A tela está desligada!')
            process = subprocess.run(
            ["adb", "-s", self.ip, "shell", "input", "keyevent", "26"],
                capture_output=True,
                text=True
            )

    def unlock_screen(self):
        process = subprocess.run(
            ["adb", "-s", self.ip, "shell", "dumpsys deviceidle | grep mScreenLocked"],
            capture_output=True,
            text=True
        )
        _, status = process.stdout.strip().split("=")
        
        if status == 'false':
            print('A tela está desbloqueada!')
        elif status == 'true':
            subprocess.run(
                ["adb", "-s", self.ip, "shell", "input", "keyevent", "26"],
            )
            sleep(1)
            w, h = self.dimensions_screen()
            subprocess.run(
                ["adb", "-s", self.ip, "shell", "input", f"swipe {w//2} {h//2} {w//2} 0 1000"],
            )
            
            
    def show_device_info(self):
        ser = subprocess.run(
            ["adb", "-s", self.ip, "shell", "getprop"],
            capture_output=True,
            text=True
        )
        device_infos = {
            "model": "ro.product.model",
            "manufacturer": "ro.product.manufacturer",
            "version": "ro.build.version.release",
            "serial_number": "ro.serialno"
        }
        
        for k,v in device_infos.items():
            process = subprocess.run(
                ["adb", "-s", self.ip, "shell", f"getprop | grep {v}"],
                capture_output=True,
                text=True
            )
            device_infos[k] = process.stdout.split("\t")[0].split()[1].strip("[]")
        
        return f"Serial_number={device_infos['serial_number']!r}, Fabricante={device_infos['manufacturer'].capitalize()!r}, Modelo={device_infos['model']!r}, Versão Android={device_infos['version']}"
        
    def open_activity(self):
        process = subprocess.run(
            ["adb", "-s", self.ip, "shell", "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'"],
            capture_output=True,
            text=True).stdout.strip('{}').split('\n')
        return process[0].split()[-1].strip('{}')
        
    def open_camera_by_package_name(self):
        process = subprocess.run(
            ["adb", "-s", self.ip, "shell", "pm list packages | grep android.app.camera"],
            capture_output=True,
            text=True
        )
        camera_pkg = process.stdout.split('\n')[0].strip().removeprefix('package:')
        subprocess.run(["adb", "-s", self.ip, "shell", f"am start -n {camera_pkg}/{camera_pkg}.Camera"])

    def go_to_home(self):
        subprocess.run(["adb", "-s", self.ip, "shell", "input keyevent 3"])

    def dimensions_screen(self):
        _, dimension = subprocess.run(
            ["adb", "-s", self.ip, "shell", "wm", "size"],
            capture_output=True,
            text=True
        ).stdout.split(':')
        w, h = dimension.strip(' \n').split('x')
        return int(w), int(h)
    
    def is_airplane_on(self):
        airplane_on = subprocess.run(
            ["adb", "-s", self.ip, "shell", "settings get global airplane_mode_on"],
            capture_output=True,
            text=True
        ).stdout.strip('\n')
        if airplane_on == '0':
            return 'Modo avião desativado!'
        elif airplane_on == '1':
            return 'Modo avião ativado!'
    
    def is_stay_awake(self):
        stay_awake = subprocess.run(
            ["adb", "-s", self.ip, "shell", "settings get global stay_on_while_plugged_in"],
            capture_output=True,
            text=True
        ).stdout.strip('\n')
        if stay_awake:
            subprocess.run(
                ["adb", "-s", self.ip, "shell", "settings put global stay_on_while_plugged_in 3"],
                capture_output=True,
                text=True
            )
    
    def tap_center(self):
        w, h = self.dimensions_screen()
        subprocess.run(
            ["adb", "-s", self.ip, "shell", "input", f"tap {w//2} {h//2}"],
            capture_output=True,
            text=True
        )
        
    def swipe_top_bot(self):
        w, h = self.dimensions_screen()
        subprocess.run(
            ["adb", "-s", self.ip, "shell", "input", f"swipe {w//2} 0 {w//2} {h} 2000"],
            capture_output=True,
            text=True
        )
    
    def all_installed_apps(self):
        packages = []
        process = subprocess.run(
            ["adb", "-s", self.ip, "shell", "pm", "list", "packages"],
            capture_output=True,
            text=True
        ).stdout
        for pkg in process.strip().split('\n'):
            packages.append(pkg)
        return len(packages)
    
if __name__ == "__main__":
    dm = DeviceManager()
    print(dm.devices_list())
    ip = input("Digite o IP e a porta do seu dispositivo <ip:port> : ")
    code = input("Digite o código de pareamento: ")
    dm.pair_device(ip, code)
    dm.connect_device()
    sleep(1)
    dm.is_screen_on()
    sleep(1)
    dm.unlock_screen()
    sleep(1)
    print(dm.dimensions_screen())
    sleep(1)
    print(dm.all_installed_apps())
    sleep(1)
    dm.open_activity()
    sleep(1)
    dm.go_to_home()
    sleep(1)
    print(dm.is_airplane_on())
    sleep(1)
    dm.swipe_top_bot()