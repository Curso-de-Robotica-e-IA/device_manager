from device_manager import DeviceManager, DeviceActions, DeviceInfo
import time

def show_devices(manager:DeviceManager):
    network_devices = manager.connector.visible_devices()
    return network_devices

def pair_code_connection(manager:DeviceManager):
    manager.adb_pairing_instance()
    code = manager.adb_pair.pair_device_with_paring_code("N3KN4M0112", "306312")
    return code

def connection_by_serial_number(manager:DeviceManager):
    manager.connector.connect_all_devices()

def mode_airplane(actions:DeviceActions=None, info:DeviceInfo =None, enable=False):
    
    actions.set_air_plane_mode(enable)

    return info.is_airplane_mode_enabled()

    
def list_all_apps_installed(info:DeviceInfo):
    return info.list_installed_all_apps()

def go_to_home(action:DeviceActions):
    action.home_button()

def dimensions_display(info:DeviceInfo):
    return info.get_screen_dimensions()

def get_info(manager:DeviceManager):
    ...

def open_camera(action:DeviceActions):
    action.camera.open()

def stay_awake(action:DeviceActions, info:DeviceInfo):
    if not info.is_stay_awake_enabled():
        return action.set_stay_awake(True)
    action.set_stay_awake(False)
def connect_to_serial_number(manager:DeviceManager):
    return manager.connector.is_connected(number)

def swipe_action(action:DeviceActions):
    action.turn_on_screen()
    time.sleep(1)
    action.swipe(10,10,300,1000,1000)
if __name__ == "__main__":
    number = "N3KN4M0112"
    manager = DeviceManager(number)
    device_info, device_action = manager[number]
    #mode_airplane(device_action, device_info)
    #go_to_home(device_action)
    #print(dimensions_display(device_info))
    #print(list_all_apps_installed(device_info))
    #print(connect_to_serial_number(manager))
    #swipe_action(device_action)
    #stay_awake(device_action, device_info)
    #print(open_camera(device_action))