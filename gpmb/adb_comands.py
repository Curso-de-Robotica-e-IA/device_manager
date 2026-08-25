
import subprocess

def receber_dispositivos():
    resultado = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    dispositivos = resultado.stdout.strip().split("\n")[1:]

    if not dispositivos:
        print("nenhum dispositivo conectado.")
    else:
        print("dispositivos conectados:")
        for dispositivo in dispositivos:
            print(dispositivo)

def emparelhar_dispositivo(ip_porta, codigo):
    try:
        resultado = subprocess.run(["adb", "pair", ip_porta],input=codigo + "\n",text=True,capture_output=True,check=True)
        print("sucesso:", resultado.stdout)
    except subprocess.CalledProcessError as e:
        print("erro ao emparelhar:", e.stderr)


def saida_dispositivos():
    saida = subprocess.check_output(["adb", "devices"]).decode().strip().split("\n")[1:]

    usb, wifi = [], []
    for linha in saida:
        if "device" in linha:
            dispositivo = linha.split()[0]
            wifi.append(dispositivo) if ":" in dispositivo else usb.append(dispositivo)

    print("USB:", usb if usb else "Nenhum")
    print("Wi-Fi:", wifi if wifi else "Nenhum")


def status_tela(serial_dispositivo):

    status_tela = "mInteractive=true" in subprocess.check_output(["adb", "-s", serial_dispositivo, "shell", "dumpsys", "power"]).decode()

    if not status_tela:
        subprocess.run(["adb", "-s", serial_dispositivo, "shell", "input", "keyevent", "224"])
        print(" A tela estava desligada e foi ligada.")
    else:
        print(" A tela ja estava ligada.")


def tela_bloqueada(serial_dispositivo):

    tela_bloqueada = "mShowingLockscreen=true" in subprocess.check_output(["adb", "-s", serial_dispositivo, "shell", "dumpsys", "window"]).decode()

    if tela_bloqueada:
        subprocess.run(["adb", "-s", serial_dispositivo, "shell", "input", "keyevent", "82"])
        print(" A tela estava bloqueada e foi desbloqueada.")
    else:
        print(" A tela não está bloqueada.")



def informacoes_dispositivos():
   resultado_serial_number = subprocess.run(["adb", "devices"], capture_output=True, text=True)
   resultado_fabricante = subprocess.run(["adb","-s", "RXCW5054NGB", "shell", "getprop", "ro.product.manufacturer"], capture_output=True, text=True)
   resultado_modelo = subprocess.run(["adb","-s", "RXCW5054NGB", "shell", "getprop", "ro.product.model"], capture_output=True, text=True)
   resultado_android_version = subprocess.run(["adb","-s", "RXCW5054NGB", "shell", "getprop", "ro.build.version.release"],capture_output=True,text=True,check=True)

   print(f"Serial Number: {resultado_serial_number.stdout.strip().splitlines()[1]}")
   print(f"Fabricante: {resultado_fabricante.stdout.strip()}")
   print(f"Modelo: {resultado_modelo.stdout.strip()}")
   print(f"Versão do Android: {resultado_android_version.stdout.strip()}")

def tela_dimessoes(serial_dispositivo):
    resultado = subprocess.run(["adb", "-s", serial_dispositivo, "shell", "wm", "size"], capture_output=True, text=True)
    print(f"Dimensões da tela do dispositivo {serial_dispositivo}: {resultado.stdout.strip()}")

def app_instaldos(serial_dispositivo):
    resultado = subprocess.run(["adb", "-s", serial_dispositivo, "shell", "pm", "list", "packages"], capture_output=True, text=True)
    print(f"Aplicativos instalados no dispositivo {serial_dispositivo}: {resultado.stdout.strip()}")

def activity_atual(serial_dispositivo):
    resultado= subprocess.run(["adb", "-s", serial_dispositivo, "shell", "dumbsys", "window"], capture_output=True, text=True)
    print(f"nome da activity atual do dispositovo {serial_dispositivo}: {resultado.stdout.strip()}")

def abrir_camera(serial_dispositivo, package, activity):
    resultado = subprocess.run(["adb", "-s", serial_dispositivo, "shell", "am", "start" ,"-n", f"{package}/{activity}"], capture_output=True, text=True)
    print(f"Abertura da câmera no dispositivo {serial_dispositivo}: {resultado.stdout.strip()}")

def home(serial_dispositivo):
    resultado = subprocess.run(["adb", "-s", serial_dispositivo, "shell", "input", "keyevent", "3"], capture_output=True, text=True)
    print(f"Indo para home do dispositivo: {serial_dispositivo}: {resultado.stdout.strip()}")

def stay_awake(serial_dispositivo):
    stay_awake = "mWakefulness=Awake" in subprocess.check_output(["adb", "-s", serial_dispositivo, "shell", "dumpsys", "power"]).decode()

    if not stay_awake:
        subprocess.run(["adb", "-s", serial_dispositivo, "shell", "input", "keyevent", "224"])
        print(" O dispositivo estava dormindo e foi acordado.")
    else:
        print(" O dispositivo já estava acordado.")

def modo_aviao(serial_dispositivo):
    modo_aviao = "mAirPlaneMode=Awake" in subprocess.check_output(["adb", "-s", serial_dispositivo, "shell", "dumpsys", "power"]).decode()
    if modo_aviao:
        print(" Modo avião está ativado")
    else:
        print("Modo avião está desativado")

def toque_na_tela(serial_dispositivo):
    tela = subprocess.check_output(["adb", "-s", serial_dispositivo, "shell", "wm", "size"]).decode().strip().split(":")[1].strip().split("x")
    largura, altura = int(tela[0]), int(tela[1])
    x = largura // 2
    y = altura // 2
    subprocess.run(["adb", "-s", serial_dispositivo, "shell", "input", "tap", str(x), str(y)])
    print(f"Toque na tela do dispositivo {serial_dispositivo}.")

def swipe(serial_dispositivo):
    tela = subprocess.check_output(["adb", "-s", serial_dispositivo, "shell", "wm", "size"]).decode().strip().split(":")[1].strip().split("x")
    largura, altura = int(tela[0]), int(tela[1])
    x = largura // 2
    subprocess.run(["adb", "-s", serial_dispositivo, "shell", "input", "swipe", str(x), "0", str(x), str(altura)])
    print(f"Swipe na tela do dispositivo {serial_dispositivo}.")

if __name__ == "__main__":
    receber_dispositivos()
    emparelhar_dispositivo("192.168.155.57:37451", "126138")
    saida_dispositivos()
    status_tela("RXCW5054NGB")
    tela_bloqueada("RXCW5054NGB")
    informacoes_dispositivos()
    tela_dimessoes("RXCW5054NGB")
    #app_instaldos("RXCW5054NGB")
    activity_atual("RXCW5054NGB")
    abrir_camera("RXCW5054NGB", "com.android.camera2", "com.android.camera.CameraLauncher")
    home("RXCW5054NGB")
    stay_awake("RXCW5054NGB")
    modo_aviao("RXCW5054NGB")
    toque_na_tela("RXCW5054NGB")
    swipe("RXCW5054NGB")


