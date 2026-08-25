import subprocess
#https://gist.github.com/Pulimet/5013acf2cd5b28e55036c82c91bd56d8

# adb devices 
# adb kill-server
# adb start-server
# adb -s ip:port/serial_number adb_command
# adb install path_to_apk
# adb pull remote local
# adb push local remote
# adb shell shell_command
# adb shell input tap X Y
# adb shell input swipe X_start Y_start X_end Y_end duration_ms
# adb shell input keyevent keycode_numeric_or_string 

# Mostrar os devices disponíveis;
# Parear device utilizando o Código de pareamento;
# Conectar device com ip e porta;
# Mostrar devices conectados via usb e via wifi;
# Verificar se a tela está ligada;
# Ligar caso desligada;
# Verificar se a tela está bloqueada;
# Desbloquear caso bloqueada;
# Mostrar o serial_number, fabricante, modelo e versão do android;

# Mostrar as dimensões da tela;
# Listar todos os apps instalados;
# Mostrar o nome da activity atual;
# Abrir a câmera pelo package e activity;
# Ir para para o home;
# Verificar se o stay awake está ativado;
# Ativar caso desativado;
# Verificar se o modo avião está ativado;
# Realizar uma ação de toque no meio da tela;
# Realizar um swipe do topo até a base da tela;

def start_server():
    return subprocess.call("adb start-server", shell=True)
#start_server()

def list_devices():
    return subprocess.call("adb devices", shell=True)
#list_devices()

def connect_device():
    return subprocess.call("adb connect 192.168.152.40", shell=True)

def connect_by_code():
    return subprocess.call("adb pair 192.168.152.40:5555", shell=True)

def verify_screen():
    result = subprocess.call(" adb shell dumpsy power", text=True, shell=True, stdout=True)
    
    if "mScreenState=ON" in result.stdout:
        return "Atela está LIGADA"
    elif "mScreenState=OFF" in result.stdout:
        return "A tela está DESLIGADA"
    else:
        return "Não foi possível determinar o estado da tela"

print(verify_screen())

def shut_screen():
    return subprocess.call("adb shell input keyevent 26", shell=True)

#shut_screen()

def turn_screen_on():
    return subprocess.call("adb shell input keyevent 224", shell=True)

#turn_screen_on()

def unlock_screen():
    return subprocess.call("adb shell locksettings set-disabled true", shell=True)

#unlock_screen()

def check_screen_blocked():
    result = subprocess.call("adb shell dumpsys window", shell = True, text=True,stdout=subprocess.PIPE )

    if "mDreamingLockscreen=true" in result:
        return True
    else:
        return False

def home():
    return subprocess.call("adb shell input keyevent 3", shell=True)

#home()

def device_info():
    result = subprocess.call("adb version", shell=True, text=True, stdout=True)
    return result

#device_info()

def open_cam():
    return subprocess.call("adb shell input keyevent 27")

#open_cam()

def touch_middle_screen():
    result = subprocess.call("adb shell input tap 540 960", shell=True)
    return result

#touch_middle_screen()

def swipe():
    result = subprocess.call("adb shell input swipe 540 234 540 2106 500", shell=True)
    return result

#swipe()

def verify_flying_mode():
    result = subprocess.call("adb shell settings get global airplane_mode_on")
    if result == 0:
        return False
    if result == 1:
        return True

#verify_flying_mode()

def stay_awake():
    result = subprocess.call("adb shell settings get global stay_on_while_plugged_in", shell = True)
    if result == 0:
        return "desativado"
    elif result == 1:

        return "Ativa"

#stay_awake()

def show_installed_apps():
    result = subprocess.call("adb shell pm list packages", shell=True)
    return result
#show_installed_apps()

def screen_size():
    result = subprocess.call("adb shell wm size", shell = True)
    return result

#screen_size()

def show_current_activity():
    result =  subprocess.call("dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'", shell=True)
    return result

#show_current_activity()



    



