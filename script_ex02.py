from device_manager import DeviceManager, AdbPairing
from time import sleep

manager = DeviceManager()  
adb_pair = AdbPairing()

def pair_with_code():
    ip = input("Digite o IP e a porta do seu dispositivo <ip:port> : ")
    code = input("Digite o código de pareamento: ")
    adb_pair.pair_device_with_paring_code(ip, code)

def connect_with_serial_number():
    manager.execute_adb_command(command='adb devices', shell=False)
    serial_number = input('Digite o serial number: ')
    device = manager.connect_devices(serial_number)
    if device[0] == serial_number:
        return { 'msg': 'Conectado com sucesso!', 'serial_number': serial_number }
    
device_info, device_action = manager['serial_number_1']  

if __name__ == "__main__":
    manager.execute_adb_command(command='adb devices', shell=False)
    #sleep(1)
    #pair_with_code()
    #sleep(1)
    connect = connect_with_serial_number()
    print(connect['msg'])
    sleep(1)
    device_info, device_action = manager[connect['serial_number']]
    w, h = device_info.get_screen_dimensions()
    if device_info.is_screen_on():
        print('Tela ligada!')
    else:
        device_action.turn_on_screen()
    device_action.swipe(w//2, h//2, w//2, 0, 2000)
    #device_action.unlock_screen() # A função unlock_screen não está desbloqueando, por este motivo utilizei o swipe
    sleep(1)
    print(device_info.get_properties())
    sleep(1)
    print(f'Width={w}, Heigth={h}')
    sleep(1)
    print(device_info.list_installed_all_apps())
    sleep(1)
    print(device_info.actual_activity())
    sleep(1)
    device_action.home_button()
    if not device_info.is_stay_awake_enabled():
        device_action.set_stay_awake(True)
    if device_info.is_airplane_mode_enabled():
        print('Modo avião ativado!')
    else:
        print('Modo avião desativado!')
    sleep(1)
    device_action.click_by_coordinates(w//2, h//2)
    sleep(1)
    device_action.swipe(w//2, 0, w//2, h, 2000)