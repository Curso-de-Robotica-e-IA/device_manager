from json import dumps

from device_manager import DeviceManager,AdbPairing,connection

manager = DeviceManager()
dict_keyevent = {f"{k}":f"KEYCODE_{k}" for k in range(10)}
dict_keyevent["power"] = "KEYCODE_POWER";dict_keyevent["enter"] = "KEYCODE_ENTER"
dict_keyevent["home"]="KEYCODE_HOME"

def update_conected_devices(devices:dict,device_list=[]):
    if len(device_list) == 0:
        device_list = list(devices.keys()) 
    for device in device_list:
        if device not in devices:
            devices[device] = {}
        devices[device]["SN"] = manager.get_device_info(device).serial_number
        devices[device]["Screen_D"] = manager.get_device_info(device).get_screen_dimensions()
        devices[device].update(manager.get_device_info(device).get_properties())   
    
    return devices


def pair_device_wifi(ip,port,key):
    manager.adb_pair.pair_device_with_paring_code(f"{ip}:{port}",key)


def checkScreenState(device):
    on = manager.get_device_info(device).is_screen_on()
    lock = manager.get_device_info(device).is_device_locked()
    if lock:
        if on:
            return "on locked"
        else:
            return "off locked"
    else:
        if on:
            return "on unlocked"
        else:
            return "off unlocked"
def turn_screen(device):
    manager.get_device_actions(device).turn_on_screen()
def unlock_device(device):
    manager.get_device_actions(device).unlock_screen()

def listApps(device):
    return manager.get_device_info(device).list_installed_all_apps()
  
def tap_action(device,points:list):
    for swipe in points:
            x = swipe["X"]
            y = swipe["Y"]
            manager.get_device_actions(device).click_by_coordinates(x,y)
        
def swipe_action(device,points:list):
    for swipe in points:
            sx = swipe["SX"]
            sy = swipe["SY"]
            ex = swipe["EX"]
            ey = swipe["EY"]
            dur = swipe["dur"]
            manager.get_device_actions(device).swipe(sx,sy,ex,ey,dur)

def home(device):
    manager.get_device_actions(device).home_button()

def current_activity(device):
    return manager.get_device_info(device).actual_activity()

def open_camera(device):
    manager.get_device_actions(device).camera.open()
    
def stay_awake(device):
    if manager.get_device_info(device).is_stay_awake_enabled():
        print(f"{device} Stay Awake is On")
    else:
        print(f"Turning {device} Stay Awake On")
        manager.get_device_actions(device).set_stay_awake(True)

def airplaneModeOn(device):
    return manager.get_device_info(device).is_airplane_mode_enabled()


print(__name__)
if __name__ == "__main__":

    for info in list(manager.connector.visible_devices()):
        manager.connect_devices(info.serial_number)
    print(dumps({line.serial_number:line.connection.name for line in list(manager.connector.visible_devices())},indent=1))
    for line in manager.connector.visible_devices(): 
        print(line)
    manager.adb_pairing_instance()
    with manager.adb_pair.pair() as qrcode_string:
        print(qrcode_string)
    print(manager)
    print(manager.connected_devices)
