from json import dumps

from device_manager import DeviceManager,AdbPairing,connection

manager = DeviceManager()
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