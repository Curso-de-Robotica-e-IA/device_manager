from subprocess import run
import argparse
from re import search

parser = argparse.ArgumentParser()

parser.add_argument("--device", required=True)
parser.add_argument("--port")
parser.add_argument("--pair_port")
parser.add_argument("--pair_code")

args = parser.parse_args()
if args.device is None or args.device.strip() == "":
    raise ValueError("Device not found")

def execute_and_collect(cmd: list[str]) -> str:
    output = run(cmd, capture_output=True, text=True)
    return output.stdout.strip() or output.stderr.strip()

def execute(cmd: list[str]) -> None:
    output = run(cmd, capture_output=True, text=True)
    print(f"{cmd} => {output.stdout.strip() or output.stderr.strip()}")
    print("#######################################################################")    

def detect_devices():
    execute(["adb", "devices"])

def pair_device_wifi():
    if args.device is not None and args.pair_code is not None:
        execute(["adb", "pair", args.device + ":" + args.pair_port, args.pair_code])

def connect_device_wifi():
    if args.port:
        execute(["adb", "connect", args.device + ":" + args.port])

def filter_connected_devices():
    devices = execute_and_collect(["adb", "devices"])
    if devices is not None and devices.strip()!= '':
        devices = devices.splitlines()[1:]
        devices = [line.split('\t')[0] for line in devices]
        wifi_devices = [device for device in devices if ':' in device]
        usb_devices = [device for device in devices if device not in wifi_devices]
        print("USB Devices:")
        print(f"{'\n'.join(usb_devices)}")
        print("Wi-Fi Paired Devices:")
        print(f"{'\n'.join(wifi_devices)}")
        print("#######################################################################")  
    else:
        raise Exception("Output not found error")
    
def detect_device_is_on():
    cmd = ['adb', '-s', args.device + ((':' + args.port) if args.port is not None else ''), 'shell', 'dumpsys power | grep mWakefulness='] # type: ignore
    status_data = execute_and_collect(cmd)
    if status_data is not None and status_data.strip() != "":
        if 'Awake' in status_data:
            print('Device is on')
        else:
            print('Device is off')
            run(['adb', '-s', args.device + ((':' + args.port) if args.port is not None else ''), 'shell', 'input keyevent 224']) # type: ignore
    else:
        raise Exception("Output not found error")
    print("#######################################################################")  

def unlock_device():
    cmd = ['adb', '-s', args.device + ((':' + args.port) if args.port is not None else ''), 'shell', 'dumpsys window policy | grep showing='] # type: ignore
    window_data = execute_and_collect(cmd)
    if window_data is not None and window_data.strip() != "":
        if 'false' in window_data:
            print('Device is unlocked')
        else:
            print('Device is locked')
            size = execute_and_collect(['adb', '-s', args.device, 'shell', 'wm size']).strip().split(":")[1].split('x')
            width = int(size[0])
            height = int(size[1])
            x = width//2
            start_y = int(height*0.85)
            end_y = int(height*0.15)
            run(["adb", "-s", args.device, "shell", "input", "swipe", f"{x}", f"{start_y}", f"{x}", f"{end_y}", "500"], check=True)
    else:
        raise Exception("Output not found error")
    print("#######################################################################")  

def grep_device_details():
    serialno = execute_and_collect(['adb', '-s', args.device, 'shell', 'getprop ro.serialno'])
    fabricante = execute_and_collect(['adb', '-s', args.device, 'shell', 'getprop ro.product.brand'])
    modelo = execute_and_collect(['adb', '-s', args.device, 'shell', 'getprop ro.product.model'])
    android = execute_and_collect(['adb', '-s', args.device, 'shell', 'getprop ro.build.version.release'])
    print("Device info: ")
    print(serialno, fabricante, modelo, "Android " + android, sep=' | ')
    print("#######################################################################")  

def screen_dimensions():
    screen = execute_and_collect(['adb', '-s', args.device, 'shell', 'wm size']).split(":")[1].strip()
    print("Screen size:")
    print(screen)
    print("#######################################################################")  

def installed_apps():
    apps: str = execute_and_collect(['adb', '-s', args.device, 'shell', 'pm list packages']).strip()

    filtered_apps: list[str] = [app.split(':')[1] for app in apps.split('\n')]
    print("Installed apps:")
    print("\n".join(filtered_apps))
    print("#######################################################################")  

def open_activity():
    activity_raw = execute_and_collect(['adb', '-s', args.device, 'shell', 'dumpsys activity activities | grep "ResumedActivity:"']).strip()
    match = search(
        r"ResumedActivity:.*?u\d+\s+([^\s]+)}",
        activity_raw,
    )
    if match is not None:
        activity: str = match.group(1)
        print("Current activity:")
        print(activity_raw)
        print(activity.split(".")[-1])
        print("#######################################################################")  
    else:
        raise Exception("Current activity not found")

def open_camera():
    execute(['adb', '-s', args.device, 'shell', 'am start -n com.motorola.odm.camera3/.CaptureActivity'])

def go_to_home():
    execute(['adb', '-s', args.device, 'shell', 'input keyevent 3'])

def is_stay_awake_on():
    is_on = execute_and_collect(['adb', '-s', args.device, 'shell', 'settings get global stay_on_while_plugged_in'])
    if is_on == '7':
        print("Stay Awake is on")
    else:
        print("Stay Awake is off")
        execute(['adb', '-s', args.device, 'shell', 'settings put global stay_on_while_plugged_in 7'])
    print("#######################################################################")  

def is_airplate_mode_on():
    is_on = execute_and_collect(['adb', '-s', args.device, 'shell', 'settings get global airplane_mode_on'])
    if is_on == '1':
        print("Airplane mode is on")
    else:
        print("Airplane mode is off")
    print("#######################################################################")  

def touch_center():
    size = execute_and_collect(['adb', '-s', args.device, 'shell', 'wm size']).strip().split(":")[1].split('x')
    width = int(size[0])
    height = int(size[1])
    execute(['adb', '-s', args.device, 'shell', f'input tap {width//2} {height//2}'])
    print("#######################################################################")  

def swipe():
    size = execute_and_collect(['adb', '-s', args.device, 'shell', 'wm size']).strip().split(":")[1].split('x')
    width = int(size[0])
    height = int(size[1])
    x = width//2
    execute(["adb", "-s", args.device, "shell", f"input swipe {x} 0 {x} {height} 500"])
    print("#######################################################################")  

detect_devices()
pair_device_wifi()
connect_device_wifi()
filter_connected_devices()
detect_device_is_on()
unlock_device()
grep_device_details()
screen_dimensions()
installed_apps()
open_activity()
open_camera()
go_to_home()
is_stay_awake_on()
is_airplate_mode_on()
touch_center()
swipe()