
from device_manager import DeviceManager
from device_manager.connection.utils.connection_type import ConnectionType

manager = DeviceManager()

devices = manager.connected_devices

def show_devices():
    """Retorna uma lista com os dispositivos conectados no adb."""
    network_devices = manager.connector.visible_devices()

    return network_devices

def connect_with_code():
    """Emparelha um novo dispositivo via Wi-Fi usando um código de autenticação."""
    manager.adb_pairing_instance()  
    qrcode = manager.adb_pair.qrcode_string

    return qrcode

def connect_with_wifi():
    """Conecta a um dispositivo Android previamente emparelhado usando rede Wi-Fi."""
    manager.adb_pairing_instance()  
    result = manager.connect_devices("RXCW5054NGB")

    return result

def show_usb_wifi_devices():
    """Separa os dispositivos conectados atualmente entre conexões USB e Wi-Fi."""
    network_devices = manager.connector.visible_devices()
    wifi_devices = []
    usb_devices = []
    for network in network_devices:
        if network.connection == ConnectionType.WIFI:
            wifi_devices.append(network)
        if network.connection == ConnectionType.USB:
            usb_devices.append(network)

    print("Dispositivos USB: ")
    for x in usb_devices:
        print(x)
    print("Dispositivos WIFI: ")
    for x in wifi_devices:
        print(x)

def wake_up_screen():
    """Verifica se a tela do dispositivo está ligada no momento."""
    for device in devices:
        info = manager.get_device_info(device)
        is_screen_on = info.is_screen_on()
        if is_screen_on:
            print("A tela já está ligada!")
        else:
            device_actions = manager.get_device_actions(device)
            device_actions.turn_on_screen()

def unlock_screen():
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
    """Imprime no console dados básicos do celular como modelo e versão do Android."""
    for device in devices:
        info = manager.get_device_info(device)
        print(f"Informações: {info.get_properties()}")

def get_phone_dimensions():
    """Identifica e retorna a resolução (largura e altura) da tela do celular."""
    for device in devices:
        info = manager.get_device_info(device)
        print(f"Dimensões: {info.get_screen_dimensions()}")

def show_installed_apps():
    """Lista todos os pacotes de aplicativos instalados no sistema Android."""
    for device in devices:
        info = manager.get_device_info(device)
        print(f"Apps instalados: {info.list_installed_all_apps()}")

def show_current_activity():
    """Busca e exibe o nome da Activity que está em foco na tela no momento."""
    for device in devices:
        info = manager.get_device_info(device)
        print(f"Atividade atual: {info.actual_activity()}")

def open_phone_camera():
    """Inicia a aplicação nativa de câmera."""
    for device in devices:
        device_actions = manager.get_device_actions(device)
        device_actions.camera.open()

def go_to_home():
    """Simula o pressionamento do botão Home."""
    for device in devices:
        device_actions = manager.get_device_actions(device)
        device_actions.home_button()


def activate_phone_awake():
    """Configura a tela para nunca desligar enquanto o cabo USB estiver conectado."""
    for device in devices:
        info = manager.get_device_info(device)
        is_awake_active = info.is_stay_awake_enabled()
        if is_awake_active:
            print("Modo awake já está ativo")
        else:
            device_actions = manager.get_device_actions(device)
            device_actions.set_stay_awake(True)
            print("Modo awake ativado com sucesso!")

def check_air_plane_mode():
    """Verifica se o modo avião está ativo no dispositivo Android."""
    for device in devices:
        info = manager.get_device_info(device)
        is_air_plane_active = info.is_airplane_mode_enabled()
        if is_air_plane_active:
            print("O modo avião está ativado")
        else:
            print("O modo avião está desativado")

def touch_middle_screen():
    """Calcula o centro exato da tela e simula um toque na coordenada."""
    for device in devices:
        info = manager.get_device_info(device)
        width, height = info.get_screen_dimensions()

        if width and height:
            center_x = width // 2
            center_y = height // 2

            device_actions = manager.get_device_actions(device)
            device_actions.click_by_coordinates(center_x, center_y)
            print("Toque realizado no centro da tela!")

def swipe_top_to_bottom():
    """Simula uma ação de arrastar o dedo de cima para baixo no centro da tela."""
    for device in devices:
        info = manager.get_device_info(device)
        width, height = info.get_screen_dimensions()

        if width and height:
            center_x = width // 2

            device_actions = manager.get_device_actions(device)
            device_actions.swipe(center_x, 0, center_x, height, 500)
            print("Swipe realizado com sucesso!")


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
# unlock_screen()

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
# activate_phone_awake()

# 14. Verificar se o modo avião está ativado
# check_air_plane_mode()

# 15. Realizar uma ação de toque no meio da tela;
# touch_middle_screen()

# 16. Realizar um swipe do topo até a base da tela
# swipe_top_to_bottom()
