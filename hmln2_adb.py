import subprocess
import re
import time

ip = "192.168.158.51"
porta = "40667"
porta_pareamento = "43081"
codigo_pareamento = "585689"

target = f"-s {ip}:{porta}"

def run_adb(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout.strip()
    except Exception:
        return "Erro de timeout"

def grep(text, pattern, ignore_case=False):
    flags = re.IGNORECASE if ignore_case else 0
    regex = re.compile(pattern, flags)
    matching_lines = [line for line in text.splitlines() if regex.search(line)]
    return matching_lines

def reiniciar_adb():
    print("=== Reiniciando Servidor ADB ===")
    run_adb("adb kill-server")
    run_adb("adb start-server")
    
    print("\n--> Dispositivos Disponíveis")
    print(run_adb("adb devices -l"))
    time.sleep(2)

def parear_e_conectar():
    print("\n--> Pareando Device")
    pareamento = run_adb(f"adb pair {ip}:{porta_pareamento} {codigo_pareamento}")
    print(pareamento)
    time.sleep(2)

    print("\n--> Conectando Via Wi-Fi")
    connection = run_adb(f"adb connect {ip}:{porta}")
    print(connection)
    time.sleep(2)

    print("\n--> Devices conectados via usb e via wi-fi")
    print(run_adb("adb devices"))
    time.sleep(2)

def estado_tela():
    print("\n--> Verificando o estado da tela")
    estado_tela = run_adb(f"adb {target} shell dumpsys deviceidle")
    greplines = grep(estado_tela, 'mScreenOn')
    
    if len(greplines) == 1:
        result = greplines[0].split('=')
        if 'false' in result:
            print('A tela está desligada, ligando...')
            run_adb(f"adb {target} shell input keyevent 26")
        elif 'true' in result:
            print('A tela está ligada.')
    else:
        print("Não foi possível mapear 'mScreenOn' neste dumpsys.")
    time.sleep(2)

def bloqueio_tela():
    print("\n--> Verificando o bloqueio da tela")
    bloqueio_tela = run_adb(f"adb {target} shell dumpsys deviceidle")
    greplines = grep(bloqueio_tela, 'mScreenLocked')
    
    if len(greplines) == 1:
        result = greplines[0].split('=')
        if 'true' in result:
            print('A tela está bloqueada, desbloqueando...')
            run_adb(f"adb {target} shell input touchscreen swipe 540 2000 540 1000")
        elif 'false' in result:
            print('A tela está desbloqueada.')
    else:
        print("Não foi possível mapear 'mScreenLocked' neste dumpsys.")
    time.sleep(2)

def infos_dispositivo():
    serial = run_adb(f"adb {target} get-serialno")
    fabricante = run_adb(f"adb {target} shell getprop ro.product.manufacturer")
    modelo = run_adb(f"adb {target} shell getprop ro.product.model")
    android_version = run_adb(f"adb {target} shell getprop ro.build.version.release")
    print(f"\nSerial: {serial}\nFabricante: {fabricante}\nModelo: {modelo}\nAndroid: {android_version}")
    time.sleep(2)

    print("\n--> Dimensões da Tela")
    print(run_adb(f"adb {target} shell wm size"))
    time.sleep(2)

    print("\nTodos os apps instalados")
    print(run_adb(f"adb {target} shell pm list packages -3")) # Printei somente os baixados pra não encher o terminal
    time.sleep(2)

def activity_atual():
    print("\n--> Activity atual")
    activity_atual = run_adb(f"adb {target} shell dumpsys activity activities")
    greplines = grep(activity_atual, 'mCurrentFocus')
    
    if len(greplines) == 0:
        print('No activity')
        return

    package_pattern = re.compile(r'com\.[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*')
    result = re.findall(package_pattern, greplines[0])
    
    if len(result) == 0:
        print('No activity')
    else:
        print('/'.join(result))
    time.sleep(2)

def interacoes():
    print("\n--> Abrindo câmera pelo package e activity")
    print(run_adb(f"adb {target} shell am start -n com.motorola.camera3/com.motorola.camera.Camera"))
    time.sleep(3)

    print("\n--> Indo para o home...")
    run_adb(f"adb {target} shell input keyevent 3")
    time.sleep(2)

    print("\n--> Verificando o stay awake")
    stay_awake = run_adb(f"adb {target} shell settings get global stay_on_while_plugged_in")
    if stay_awake == '0':
        print("Stay awake está desativado, ativando...")
        run_adb(f"adb {target} shell settings put global stay_on_while_plugged_in 3")
    elif stay_awake == '3':
        print("Stay está awake ativado.")
    time.sleep(2)

    print("\n--> Verificando o modo avião")
    modo_aviao = run_adb(f"adb {target} shell settings get global airplane_mode_on")
    if modo_aviao == '1':
        print("Modo avião está ativado.")
    elif modo_aviao == '0':
        print("Modo avião está desativado.")
    time.sleep(2)

    print("\n--> Relizando uma ação de toque no meio da tela")
    run_adb(f"adb {target} shell input tap 540 1200")
    time.sleep(2)

    print("\n--> Realizando um swipe do topo até a base da tela")
    run_adb(f"adb {target} shell input swipe 540 0 540 2400 500")

if __name__ == "__main__":
    reiniciar_adb()
    parear_e_conectar()
    estado_tela()
    bloqueio_tela()
    infos_dispositivo()
    activity_atual()
    interacoes()
