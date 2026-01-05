from device_manager import DeviceManager

manager = DeviceManager()

all_devices = manager.connector.list_all_devices()
print('All connected devices:', all_devices)

manager.update_authorized_list()
print('All authorized devices:', manager.authorized_devices)
for device in manager.authorized_devices:
    info = manager.get_device_info(device)
    print(info.get_properties())
    actions = manager.get_device_actions(device)
    actions.home_button()

manager.execute_adb_command('input keyevent 3', manager.authorized_devices)

manager.clear()
