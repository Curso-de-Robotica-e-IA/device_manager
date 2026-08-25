from json import dumps

from device_manager import DeviceManager,AdbPairing,connection

manager = DeviceManager()
dict_keyevent = {f"{k}":f"KEYCODE_{k}" for k in range(10)}
dict_keyevent["power"] = "KEYCODE_POWER";dict_keyevent["enter"] = "KEYCODE_ENTER"
dict_keyevent["home"]="KEYCODE_HOME"

def update_conected_devices(devices:dict,device_list=[]):
    # manager.connect_devices()
    # for device in manager:
    #     i = 1
    #     device.info
    if len(device_list) == 0:
        device_list = list(devices.keys()) 
    for device in device_list:
        if device not in devices:
            devices[device] = {}
        devices[device]["SN"] = manager.get_device_info(device).serial_number
        devices[device]["Screen_D"] = manager.get_device_info(device).get_screen_dimensions()
        devices[device].update(manager.get_device_info(device).get_properties())   
    
    return devices


def build_Comand(d):
    pass

def pair_device_wifi(ip,port,key):
    manager.adb_pair.pair_device_with_paring_code(f"{ip}:{port}",key)

screen_state = {}
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
    # manager.execute_adb_command(f"shell input keyevent {dict_keyevent['enter']}")
    manager.get_device_actions(device).unlock_screen()
    # for k in list(str(key)):
    #     manager.get_device_actions(device)
    #     manager.execute_adb_command(f"shell input keyevent {dict_keyevent[k]}")

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
    
    l = list(manager.connector.visible_devices())
    manager.connector.connect_all_devices()
    # for line in manager.connector.visible_devices(): 
    #     print(line)
    #     sn = line.serial_number
        
    #     manager.connect_devices(sn)
    print(dumps({},indent=1))
    #connector =  connection.
    #manager.adb_pair.set_password()
    manager.adb_pairing_instance()

    #manager.connector.connection.
    with manager.adb_pair.pair() as qrcode_string:
        # Show the QRCode in a window, or print it in the terminal
        print(qrcode_string)
        # manager.adb_pair.generate_qrcode_string
        #manager.connector.connection.device_pairing(10)
    #qrcode = manager.adb_pair.qrcode_string  # (2)!

    #manager.connect_devices("RQCRA00NL6D")
    #manager.connect_devices("RQCRA00NL6D")
    print(manager)
    print(manager.connected_devices)
    #manager.adb_pair()
    #manager.disconnect_devices()
    #print(f"{dev.__class__}\n{dev}")