from device_manager import DeviceManager

manager = DeviceManager()

all_devices = manager.connector.list_all_devices()
print("All connected devices:", all_devices)

network_devices = manager.connect_devices()
print(network_devices)
print(manager.connected_devices)
for device in manager.connected_devices:
    info = manager.get_device_info(device)
    print(info.get_properties())
    actions = manager.get_device_actions(device)
    actions.home_button()

manager.execute_adb_command("input keyevent 3",manager.connected_devices, )

manager.clear()

