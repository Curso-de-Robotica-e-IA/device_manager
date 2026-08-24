import argparse

from device_manager import actions
from device_manager.connection.utils.connection_type import ConnectionType
from device_manager.manager import DeviceManager
from device_manager.manager_singleton import DeviceManagerSingleton

parser = argparse.ArgumentParser()

parser.add_argument("--device", required=True)
parser.add_argument("--port")
parser.add_argument("--pair_port")
parser.add_argument("--pair_code")

args = parser.parse_args()
if args.device is None or args.device.strip() == "":
    raise ValueError("Device not found")

if args.port is not None:
    manager = DeviceManager(fixed_port=args.port)
else:
    manager = DeviceManager()

def detect_devices():
    print(manager.connected_devices)
    print("#######################################################################")  

def pair_device_wifi():
    if args.device is not None and args.pair_code is not None:
        manager.adb_pairing_instance()
        if manager.adb_pair is not None:
            paired = manager.adb_pair.pair_device_with_paring_code(args.device + ":" + args.pair_port, args.pair_code)
            if not paired:
                raise Exception("Error when connecting pairing code")
            print(paired)
        else:
            raise Exception("adb pairing not working")
        print("#######################################################################")  

def connect_device_wifi():
    manager.connector.start_connection([args.device])
    print("#######################################################################")  

def filter_connected_devices():
    print(manager.connected_devices)
    usb = []
    wifi = []
    for device in manager.connected_devices:
        info = manager.get_device_info(device)
        connection = info.device_connection.connection_info[device]
        if connection is None:
            continue
        if connection.connection is ConnectionType.WIFI:
            wifi.append(device)
        if connection.connection is ConnectionType.USB:
            usb.append(device)

    print("USB Devices:")
    print(usb)
    print("Wi-Fi Devices:")
    print(wifi)
    print("#######################################################################")  
def detect_device_is_on():
    device = manager.get_device_info(args.device)
    print(device.is_screen_on())
    if not device.is_screen_on():
        action = manager.get_device_actions(args.device)
        action.turn_on_screen()
    print("#######################################################################")  

def unlock_device():
    device = manager.get_device_info(args.device)
    print(device.is_device_locked())
    if device.is_device_locked():
        action = manager.get_device_actions(args.device)
        action.unlock_screen()
    print("#######################################################################")  

def grep_device_details():
    device = manager.get_device_info(args.device)
    props = device.get_properties()
    print(*props.values(), sep=" | ")
    print("#######################################################################")  

def screen_dimensions():
    device = manager.get_device_info(args.device)
    print(device.get_screen_dimensions())
    print("#######################################################################")  

def installed_apps():
    device = manager.get_device_info(args.device)
    print(device.list_installed_all_apps())
    print("#######################################################################")  

def open_activity():
    device = manager.get_device_info(args.device)
    print(device.actual_activity())
    print("#######################################################################")  

def open_camera():
    action = manager.get_device_actions(args.device)
    action.open_app('com.motorola.odm.camera3', '.CaptureActivity')
    print("#######################################################################")  

def go_to_home():
    action = manager.get_device_actions(args.device)
    action.home_button()
    print("#######################################################################")  

def is_stay_awake_on():
    device = manager.get_device_info(args.device)
    print(device.is_stay_awake_enabled())
    if not device.is_stay_awake_enabled():
        action = manager.get_device_actions(args.device)
        action.set_stay_awake(True)
    print("#######################################################################")  

def is_airplate_mode_on():
    device = manager.get_device_info(args.device)
    print(device.is_airplane_mode_enabled())
    print("#######################################################################")  

def touch_center():
    device = manager.get_device_info(args.device)
    actions = manager.get_device_actions(args.device)
    width, heigth = device.get_screen_dimensions()
    actions.click_by_coordinates(width // 2, heigth // 2)
    print("#######################################################################")  

def swipe():
    device = manager.get_device_info(args.device)
    actions = manager.get_device_actions(args.device)
    width, heigth = device.get_screen_dimensions()
    actions.swipe(width // 2, 0, width // 2, heigth, 500)
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