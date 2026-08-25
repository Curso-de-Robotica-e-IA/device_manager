from device_manager import DeviceManager, DeviceInfo, DeviceActions, AdbPairing
from device_manager.connection.device_connection import DeviceConnection, ConnectionType

import time


MY_SERIAL_NUMBER = "d36e54d8"
MY_PAIRING_CODE = "641065"







def show_available_devices():
    network_devices = manager.connector.visible_devices() #Shows all
    print(f'Available devices : {network_devices}')


def pair_using_code(ip_port : str = "192.168.158.45:41993", pair_code : str = "641065"):
    pairing_result = pairing_server.pair_device_with_paring_code(ip_port,pair_code)
    print(pairing_result)


def connect_using_serial_number():
    print("Starting connection")
    result = manager.connector.start_connection([MY_SERIAL_NUMBER])
    print(result)


def show_connected_devices():
    wifi = []
    usb = []
    network_devices = manager.connector.visible_devices() #Shows all
    #print(f'Available devices : {network_devices}')

    my_connected_devices = manager.connected_devices

    print(f'My connected devices are : {my_connected_devices}')

    for dev in network_devices:
        if not (dev.serial_number in my_connected_devices):
            continue
        if dev.connection == ConnectionType.WIFI:
            wifi.append(dev)
        elif dev.connection == ConnectionType.USB:
            usb.append(dev)
        else:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("Device in devices is neither usb or wifi connection")

    print(f'Wifi devices : {wifi}')
    print(f'USB devices : {usb}')


def check_screen_state():

    if device_info.is_screen_on():
        print("Screen state : ON")
    else:
        print("Screen state : OFF. Turning it on now...")
        time.sleep(2)
        device_action.turn_on_screen()


def check_screen_block():
    if device_info.is_device_locked():
        print("Screen is locked. Unlocking it now...")
        time.sleep(2)
        device_action.unlock_screen() #Not working properly. Talked with Jefferson about it.
    else:
        print("Screen is unlocked.")


def show_device_info():
    device_prop = device_info.get_properties()
    print(f'Device information : {device_prop}')


def show_screen_dimensions():
    print(f"Screen size : {device_info.get_screen_dimensions()}")


def show_installed_apps():
    print(f'Apps : {device_info.list_installed_all_apps()}')


def show_current_activity():
    print(f'Current activity : {device_info.actual_activity()}')


def open_camera():
    print("Opening Camera now...")
    time.sleep(2)
    camera_package = 'com.android.camera/com.android.camera.Camera'
    device_action.open_app(camera_package)


def go_to_home():
    print("Going to home...")
    time.sleep(1)
    device_action.home_button()


def check_stay_awake():
    print("Checking stay awake.")
    if device_info.is_stay_awake_enabled():
        print("Stay awake mode is enabled.")
    else:
        print("Stay awake mode is disabled. Enabling it now.")
        device_action.set_stay_awake(True)


def check_airplane_mode():
    print("Checking airplane mode.")
    if device_info.is_airplane_mode_enabled():
        print("Airplane is enabled.")
    else:
        print("Airplane mode is disabled.")


def touch_middle_screen():
    print("Starting action : Tap middle screen")
    time.sleep(2)
    device_action.click_by_coordinates(1080/2, 2400/2)


def swipe_down():
    print("Starting action : swipe")
    time.sleep(2)
    device_action.swipe(540, 20, 540, 2300, 2000)



manager = DeviceManager()
manager.connect_devices(MY_SERIAL_NUMBER)
device_info, device_action = manager[MY_SERIAL_NUMBER] 

pairing_server = AdbPairing()
pairing_server.start()


show_available_devices()

#pair_using_code("192.168.158.45:41735", "334122") #Remove comment '#' to run it.
#connect_using_serial_number() #Remove comment to run it. 


show_connected_devices()

check_screen_state()
check_screen_block()
show_device_info()
show_screen_dimensions()
show_installed_apps()
show_current_activity()
open_camera()
go_to_home()
check_stay_awake()
check_airplane_mode()
touch_middle_screen()
swipe_down()




