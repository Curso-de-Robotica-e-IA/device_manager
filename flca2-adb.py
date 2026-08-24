import subprocess
import time

ADB_PATH = r"C:\Users\flca2\Documents\platform-tools\adb.exe"

IP_ADDRESS = "192.168.158.21"
DEVICE = ["-s", "RQCX805H9MZ"]
PIN = 1415

def run_adb(command):
    try:
        result = subprocess.run([ADB_PATH] + DEVICE + command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando ADB {command}: {e.stderr}")
        return None

def show_devices():
    result = run_adb(["devices"])
    return result

def connect_with_code():
    result = run_adb(["pair", f"{IP_ADDRESS}:38189", "922152"])
    return result

def connect_with_wifi():
    result = run_adb([f"connect", f"{IP_ADDRESS}:36255"])
    return result

def show_usb_wifi_devices():
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

    return usb_devices, wifi_devices

def is_screen_on():
    result = run_adb(["shell", "dumpsys", "power"])
    if not result:
        return False
    return "mHoldingDisplaySuspendBlocker=true" in result

def wake_up_screen():
    if not is_screen_on():
        print("Ligando a tela...")
        run_adb(["shell", "input", "keyevent", "26"])
    else:
        print("A tela já está ligada.")

def is_screen_locked():
    """Verifica se a tela de bloqueio está ativa."""
    result = run_adb(["shell", "dumpsys", "window"])
    if not result:
        return False
    return "mShowing=true" in result or "mDreamingLockscreen=true" in result

def unlock_screen_with_pin():
    """Garante que a tela está ligada e desbloqueia se necessário."""
    wake_up_screen()
    
    if not is_screen_locked():
        print("A tela já está desbloqueada.")
        return "Tela já estava desbloqueada."
        
    print("Tela bloqueada. Iniciando processo de PIN...")

    run_adb(["shell", "wm", "dismiss-keyguard"])
    time.sleep(0.5)

    print(f"Digitando o PIN...")
    run_adb(["shell", "input", "text", str(PIN)])
    time.sleep(0.5)

    run_adb(["shell", "input", "keyevent", "66"])
    time.sleep(0.5)


# 1. Mostrar os devices disponíveis
# print(show_devices())

# 2. Parear device utilizando o Código de pareamento
# print(connect_with_code())

# 3. Conectar device com ip e porta
# print(connect_with_wifi())

# 4. Mostrar devices conectados via usb e via wifi
# usb, wifi = show_usb_wifi_devices()
# print("Dispositivos USB: ")
# for x in usb:
#     print(x)
# print("Dispositivos WIFI: ")
# for x in wifi:
#     print(x)

# 5. Verificar se a tela está ligada; Ligar caso desligada;
# wake_up_screen()

# 6. Verificar se a tela está bloqueada; Desbloquear caso bloqueada;
# unlock_screen_with_pin()


