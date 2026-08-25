import time
from device_manager import DeviceManager
from device_manager.connection.utils.connection_type import ConnectionType

manager = DeviceManager()

MY_SERIAL_NUMBER = "ZF5246RQKB"

print("\n--> Devices disponíveis")
network_devices = manager.connector.visible_devices()
for device in network_devices:
    print(f"Serial={device.serial_number} | IP={device.ip}:{device.port}")

time.sleep(1)

print("\n--> Pareando Device")
manager.adb_pairing_instance()
if manager.adb_pair:
    try:
        manager.adb_pair.pair_device_with_paring_code("192.168.158.51:40599", "239188")
        print("Dispositivo pareado.")
    except Exception as e:
        print(f"Falha: {e}")

time.sleep(2)

print("\n--> Conectando device pelo serial number")
manager.connect_devices(MY_SERIAL_NUMBER)  

device_info, device_action = manager[MY_SERIAL_NUMBER]

time.sleep(1)

print("\n--> Dispositivos conectados via usb e via wifi:")
for device in manager.connector.visible_devices():
    if device.serial_number == MY_SERIAL_NUMBER:
        if device.connection == ConnectionType.USB:
            print(f"USB: Serial={device.serial_number} | IP={device.ip}:{device.port}")
        elif device.connection == ConnectionType.WIFI:
            print(f"WIFI: Serial={device.serial_number} | IP={device.ip}:{device.port}")

time.sleep(1)

print("\n--> Verificando o estado da tela")
if not device_info.is_screen_on():
    print("Tela está desligada, ligando...")
    device_action.turn_on_screen()
else:
    print("Tela está ligada.")

time.sleep(2)

print("\n--> Verificando o bloqueio da tela")
if device_info.is_device_locked():
    print("Tela está bloqueada, desbloqueando...")
    device_action.unlock_screen()
else:
    print("Tela está desbloqueada.")

time.sleep(2)

print("\n--> Propriedades do dispositivo")
print(device_info.get_properties())

time.sleep(1)

print("\n--> Dimensões da Tela")
print(device_info.get_screen_dimensions())

time.sleep(1)

print("\nTodos os apps instalados")
print(device_info.list_installed_all_apps())

time.sleep(1)

print("\n--> Activity atual")
print(device_info.actual_activity())

time.sleep(2)

print("\n--> Abrindo câmera pelo package e activity")
device_action.open_app("com.motorola.camera3", "com.motorola.camera.Camera")

time.sleep(3)

print("\n--> Indo para o home...")
device_action.home_button()

time.sleep(2)

print("\n--> Verificando o stay awake")
if not device_info.is_stay_awake_enabled():
    print("Stay awake desativado, ativando...")
    device_action.set_stay_awake(True)
else:
    print("Stay awake está ativado.")

time.sleep(1)

print("\n--> Verificando o modo avião")
if device_info.is_airplane_mode_enabled():
    print("Modo avião está ativado.")
else:
    print("Modo avião está desativado.")

time.sleep(2)

print("\n--> Relizando uma ação de toque no meio da tela")
device_action.click_by_coordinates(540, 1200)

time.sleep(2)

print("\n--> Realizando um swipe do topo até a base da tela")
device_action.swipe(540, 0, 540, 2400, 500)