import subprocess
import time
import re

ADB_PATH = r"C:\Users\flca2\Documents\platform-tools\adb.exe"

IP_ADDRESS = "192.168.158.21"
DEVICE = ["-s", "RQCX805H9MZ"]
PIN = 1415

def run_adb(command):
    """Executa um comando ADB no dispositivo Android conectado."""
    try:
        result = subprocess.run([ADB_PATH] + DEVICE + command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando ADB {command}: {e.stderr}")
        return None

def show_devices():
    """Retorna o texto bruto com a lista de dispositivos reconhecidos pelo ADB."""
    result = run_adb(["devices"])
    return result

def connect_with_code():
    """Emparelha um novo dispositivo via Wi-Fi usando um código de autenticação."""
    result = run_adb(["pair", f"{IP_ADDRESS}:38189", "922152"])
    return result

def connect_with_wifi():
    """Conecta a um dispositivo Android previamente emparelhado usando rede Wi-Fi."""
    result = run_adb([f"connect", f"{IP_ADDRESS}:36255"])
    return result

def show_usb_wifi_devices():
    """Separa os dispositivos conectados atualmente entre conexões USB e Wi-Fi."""
    result = show_devices()
    usb_devices = []
    wifi_devices = []

    rows = result.strip().split('\n')
    rows_dispositivos = rows[1:]
    
    for linha in rows_dispositivos:
        if linha.strip():
            partes = linha.split('\t')
            serial = partes[0]
            status = partes[1]
            
            if status == 'device':
                if '_adb-tls-connect' in serial or (':' in serial and len(serial.split('.')) == 4):
                    wifi_devices.append(serial)
                else:
                    usb_devices.append(serial)

    print("Dispositivos USB: ")
    for x in usb_devices:
        print(x)
    print("Dispositivos WIFI: ")
    for x in wifi_devices:
        print(x)

    return usb_devices, wifi_devices

def is_screen_on():
    """Verifica se a tela do dispositivo está ligada no momento."""
    result = run_adb(["shell", "dumpsys", "power"])
    if not result:
        return False
    return "mHoldingDisplaySuspendBlocker=true" in result

def wake_up_screen():
    """Acorda a tela do dispositivo enviando o comando do botão Power."""
    if not is_screen_on():
        print("Ligando a tela...")
        run_adb(["shell", "input", "keyevent", "26"])
    else:
        print("A tela já está ligada.")

def is_screen_locked():
    """Verifica se a tela de bloqueio (Keyguard) do dispositivo está ativa."""
    result = run_adb(["shell", "dumpsys", "window"])
    if not result:
        return False
    return "mShowing=true" in result or "mDreamingLockscreen=true" in result

def unlock_screen_with_pin():
    """Executa a rotina completa de ligar a tela e digitar o PIN de desbloqueio."""
    wake_up_screen()
    
    if not is_screen_locked():
        print("A tela já está desbloqueada.")
        return True
        
    print("Tela bloqueada. Iniciando processo de PIN...")

    run_adb(["shell", "wm", "dismiss-keyguard"])
    time.sleep(0.5)

    print(f"Digitando o PIN...")
    run_adb(["shell", "input", "text", str(PIN)])
    time.sleep(0.5)

    run_adb(["shell", "input", "keyevent", "66"])
    time.sleep(0.5)

    if not is_screen_locked():
        print("Tela desbloqueada com sucesso via PIN!")
        return True
    else:
        print("Falha ao desbloquear.")
        return False

def show_phone_info():
    """Imprime no console dados básicos do celular como modelo e versão do Android."""
    phone_info = {
        'serial_number': run_adb(["get-serialno"]),
        'manufacturer': run_adb(["shell", "getprop", "ro.product.manufacturer"]),
        'model': run_adb(["shell", "getprop", "ro.product.model"]),
        'android_version': run_adb(["shell", "getprop", "ro.build.version.release"])
    }   

    for key, value in phone_info.items():
        print(f'{key}: {value}')

def get_phone_dimensions():
    """Identifica e retorna a resolução (largura e altura) da tela do celular."""
    result = run_adb(["shell", "wm", "size"])
    match = re.search(r'(\d+)x(\d+)', result)
    if match:
        width = int(match.group(1))
        height = int(match.group(2))
        print(f"As dimensões da tela são {width}x{height}")
        return (width, height)

def show_installed_apps():
    """Lista todos os pacotes de aplicativos instalados no sistema Android."""
    result = run_adb(["shell", "cmd", "package", "list", "packages"])
    print(result)

def show_current_activity():
    """Busca e exibe o nome da Activity que está em foco na tela no momento."""
    result = run_adb(["shell", "dumpsys", "window", "windows"])

    for line in result.splitlines():
        if "mCurrentFocus" in line:
            print(line.strip())
            return
            
    print("Activity atual não encontrada.")

def open_phone_camera():
    """Desbloqueia o dispositivo e inicia a aplicação nativa de câmera."""
    if(unlock_screen_with_pin()):
        run_adb(["shell", "am", "start", "-a", "android.media.action.STILL_IMAGE_CAMERA"])

def go_to_home():
    """Desbloqueia o dispositivo e simula o pressionamento do botão Home."""
    if(unlock_screen_with_pin()):
        run_adb(["shell", "input", "keyevent", "3"])

def activate_phone_awake():
    """Configura a tela para nunca desligar enquanto o cabo USB estiver conectado."""
    is_awake = run_adb(["shell", "settings", "get", "global", "stay_on_while_plugged_in"]) != '0'

    if is_awake:
        print("Modo awake já está ativo")
    else:
        run_adb(["shell", "settings", "put", "global", "stay_on_while_plugged_in", "3"])
        print("Modo awake ativado com sucesso!")

def check_air_plane_mode():
    """Verifica se o modo avião está ativo no dispositivo Android."""
    is_air_plane_active = run_adb(["shell", "settings", "get", "global", "stay_on_while_plugged_in"]) != '3'

    if is_air_plane_active:
        print("O modo avião está ativado")
    else:
        print("O modo avião está desativado")

def touch_middle_screen():
    """Calcula o centro exato da tela e simula um toque na coordenada."""
    width, height = get_phone_dimensions()

    if width and height:
        center_x = width // 2
        center_y = height // 2

        run_adb(["shell", "input", "tap", str(center_x), str(center_y)])
        print("Toque realizado no centro da tela!")

def swipe_top_to_bottom():
    """Simula uma ação de arrastar o dedo de cima para baixo no centro da tela."""
    width, height = get_phone_dimensions()
    
    if width and height:
        center_x = width // 2

        run_adb(["shell", "input", "swipe", str(center_x), str(0), str(center_x), str(height), '500'])
        print("Toque realizado no centro da tela!")


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
# activate_phone_awake()

# 14. Verificar se o modo avião está ativado
# check_air_plane_mode()

# 15. Realizar uma ação de toque no meio da tela;
# touch_middle_screen()

# 16. Realizar um swipe do topo até a base da tela
# swipe_top_to_bottom()
