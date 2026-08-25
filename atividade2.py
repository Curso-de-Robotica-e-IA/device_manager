from device_manager import DeviceManager
import time
#instanciando o device manager
manager = DeviceManager()  
#exibindo os devices disponíveis


print("exibindos os dispositivos visíveis")
network_devices = manager.connector.visible_devices()
for device in network_devices:
    print(device)

#pareando
# ip_porta = '192.168.155.64:37911'
# pairing_code = '671796'

ip_porta = input("Digite o IP e a porta disponíveis na tela do dispositivo")
pairing_code = input('digite o pairing code')
manager.adb_pairing_instance()  
if(manager.adb_pair.pair_device_with_paring_code(ip_porta,pairing_code)):
    print("dispositivo pareado")

manager.connect_devices('e8fbf133')
network_devices = manager.connector.visible_devices()
for device in network_devices:
    print(device)

time.sleep(3)
print("====================================================================")
for device in manager:
    if(device.serial_number=="e8fbf133"):
        informacoes = device.device_info  
        acoes = device.device_actions
        if(not informacoes.is_screen_on()):
            acoes.turn_on_screen()
        if(informacoes.is_device_locked()):
            acoes.unlock_screen()
        print(informacoes.get_properties())
        print(informacoes.get_screen_dimensions())
        print(informacoes.list_installed_all_apps())
        print(informacoes.actual_activity())
        acoes.open_app('com.android.camera','com.android.camera.Camera')
        acoes.home_button()
        if(not informacoes.is_stay_awake_enabled()):
            acoes.set_stay_awake(True)
        if(informacoes.is_airplane_mode_enabled()):
            print("o modo aviao esta ligado")
        time.sleep(1)
        acoes.click_by_coordinates(520 ,1200)
        time.sleep(1)
        acoes.swipe(540, 0, 540, 2100,1000)
