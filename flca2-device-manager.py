
from device_manager import DeviceManager
import time
import re

manager = DeviceManager()

devices = manager.connected_devices

def show_devices():
    network_devices = manager.connector.visible_devices()

    return network_devices

def connect_with_code():
    manager.adb_pairing_instance()  
    qrcode = manager.adb_pair.qrcode_string

    return qrcode

def connect_with_wifi():
    manager.adb_pairing_instance()  
    result = manager.connect_devices("RXCW5054NGB")

    return result

def show_usb_wifi_devices():
    result = manager.connected_devices
    print("🚀 ~ show_usb_wifi_devices ~ result:", manager.get_device_info(result[0]))

def wake_up_screen():
    for device in devices:
        info = manager.get_device_info(device)
        is_screen_on = info.is_screen_on()
        if is_screen_on:
            print("A tela já está ligada!")
        else:
            device_actions = manager.get_device_actions(device)
            device_actions.turn_on_screen()

def unlock_screen_with_pin():
    """Garante que a tela está ligada e desbloqueia se necessário."""
    for device in devices:
        info = manager.get_device_info(device)
        is_locked = info.is_device_locked()
        if not is_locked:
            print("A tela já está ligada!")
        else:
            device_actions = manager.get_device_actions(device)
            device_actions.unlock_screen()

def show_phone_info():
    for device in devices:
        info = manager.get_device_info(device)
        print(f"Informações: {info.get_properties()}")

def get_phone_dimensions():
    for device in devices:
        info = manager.get_device_info(device)
        print(f"Dimensões: {info.get_screen_dimensions()}")

def show_installed_apps():
    for device in devices:
        info = manager.get_device_info(device)
        print(f"Apps instalados: {info.list_installed_all_apps()}")

def show_current_activity():
    for device in devices:
        info = manager.get_device_info(device)
        print(f"Atividade atual: {info.actual_activity()}")

def open_phone_camera():
    for device in devices:
        device_actions = manager.get_device_actions(device)
        device_actions.camera.open()

def go_to_home():
    for device in devices:
        device_actions = manager.get_device_actions(device)
        device_actions.home_button()


def activate_phone_awake():
    for device in devices:
        info = manager.get_device_info(device)
        is_locked = info.is_device_locked()
        if not is_locked:
            print("A tela já está ligada!")
        else:
            device_actions = manager.get_device_actions(device)
            device_actions.unlock_screen()

# def check_air_plane_mode():
#     on_air_plane_mode = run_adb(["shell", "settings", "get", "global", "stay_on_while_plugged_in"]) != '3'

#     if on_air_plane_mode:
#         print("O dispositivo está no modo avião")
#     else:
#         print("O dispositivo não está no modo avião")

# def touch_middle_screen():
#     width, height = get_phone_dimensions()

#     if width and height:
#         center_x = width // 2
#         center_y = height // 2

#         run_adb(["shell", "input", "tap", str(center_x), str(center_y)])
#         print("Toque realizado no centro da tela!")

# def swipe_top_to_bottom():
#     width, height = get_phone_dimensions()
    
#     if width and height:
#         center_x = width // 2

#         run_adb(["shell", "input", "swipe", str(center_x), str(0), str(center_x), str(height), '500'])
#         print("Toque realizado no centro da tela!")


# 1. Mostrar os devices disponíveis
# print(show_devices())

# 2. Parear device utilizando o Código de pareamento
# print(connect_with_code())

# 3. Conectar device com ip e porta
# print(connect_with_wifi())

# 4. Mostrar devices conectados via usb e via wifi
# show_usb_wifi_devices()

# 5. Verificar se a tela está ligada; Ligar caso desligada;
# wake_up_screen()

# 6. Verificar se a tela está bloqueada; Desbloquear caso bloqueada;
# unlock_screen_with_pin()

# 7. Mostrar o serial_number, fabricante, modelo e versão do android
# show_phone_info()

# 8. Mostrar as dimensões da tela
# get_phone_dimensions()

# 9. Listar todos os apps instalados
# show_installed_apps()

# 10. Mostrar o nome da activity atual
# show_current_activity()

# 11. Abrir a câmera pelo package e activity
# open_phone_camera()

# 12. Ir para para o home
# go_to_home()

# 13. Verificar se o stay awake está ativado; Ativar caso desativado;
activate_phone_awake()

# 14. Verificar se o modo avião está ativado
# check_air_plane_mode()

# 15. Realizar uma ação de toque no meio da tela;
# touch_middle_screen()

# 16. Realizar um swipe do topo até a base da tela
# swipe_top_to_bottom()
