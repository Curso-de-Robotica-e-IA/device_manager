import subprocess
import time

#Comando de "quem está aí?"
def mostrar_conexoes():
    digita_comando = subprocess.run(["adb", "devices"])

    #tratamento de linhas limpando espaços vazios e separando elas por quebra de linha
    linhas = digita_comando.stdout.strip().split("\n")

    dispositivos_usb = []
    dispositivos_wifi = []

    # A primeira linha é apenas o cabeçalho "List of devices attached"
    for linha in linhas[1:]:
        if not linha.strip():
            continue

        partes = linha.split()
        serial_ou_ip = partes[0]
        status = partes[1]    

        if status == "device":
            if ":" in serial_ou_ip and serial_ou_ip[0].isdigit():
                dispositivos_usb.append(linha)
            else:
                dispositivos_wifi.append(linha)

    print("DISPOSITIVOS VIA USB (SERIAL):")
    for usb in dispositivos_usb:
        print(f"  • Serial: {usb}")
    if not dispositivos_usb:
        print(" (Nenhum dispositivo USB)")

    print("DISPOSITIVOS VIA REDE (IP):")
    for rede in dispositivos_wifi:
        print(f"  • IP: {rede}")
    if not dispositivos_wifi:
        print(" (Nenhum dispositivo via Rede)")


SERIAL_DO_CELULAR = "RX8Y3014GAX" 

def conexao_por_serial():
    print(f"Conectando dispositivo com o Serial: {SERIAL_DO_CELULAR}...")
    
    try:
            digita_comando = subprocess.run(
            ["adb", "-s", SERIAL_DO_CELULAR]
        )
    except subprocess.TimeoutExpired:
        print("O comando do ADB demorou muito para responder.")
         

#Conexão via WIFI com IP:PORTA
def conexao_por_wifi():
    ip_dispositivo = "192.168.158.42:43533"
    try:
        digita_comando_wifi = subprocess.run(["adb", "connect", ip_dispositivo])
        print("Dispositivos conectados (wifi):")
        print(digita_comando_wifi)
    except subprocess.TimeoutExpired:
        print("O comando do ADB demorou muito para responder.")



def ligar_tela():
    comando_status_tela = ["adb", "shell", "dumpsys", "power"]
    digita_comando = subprocess.run(comando_status_tela, capture_output=True)
    saida = digita_comando.stdout

    if "Asleep" in saida or "Dozing" in saida:
        print("A tela está desligada. Ligando...")
        subprocess.run(["adb", "shell", "input", "keyevent", "224"])
    else:
        print("A tela já está ligada. Nenhuma ação necessária.")    

def desbloquear_tela():
    print("Acordando a tela...")
    subprocess.run(["adb", "shell", "input", "keyevent", "224"])
    time.sleep(0.5)

    print("Deslizando para abrir teclado do PIN...")
    subprocess.run(["adb", "shell", "input", "swipe", "300", "1000", "300", "400", "300"])
    time.sleep(0.5)

    print(f"Digitando o PIN...")
    subprocess.run(["adb", "shell", "input", "text", str('1903')])
    time.sleep(0.3)

    print("Confirmando...")
    subprocess.run(["adb", "shell", "input", "keyevent", "66"])
    print("Aparelho desbloqueado!")

def mostrar_dados():
    dados = {}
    
     # 1. Captura o Serial Number (ignora cabeçalho do 'adb devices')
    digita_comando = subprocess.run(["adb", "devices"],capture_output=True, text=True)
    linhas = digita_comando.stdout.strip().split("\n")

    if len(linhas) > 1 and "device" in linhas[1]:
            linha = linhas[1]
            serial_device = linha.split()
            dados["serial_number"] = serial_device[0]
    else:
            dados["serial_number"] = "Não encontrado ou desconectado"

    digita_comando_fabricante = subprocess.run(["adb", "shell", "getprop", "ro.product.manufacturer"], capture_output=True, text=True)
    dados["fabricante"] = digita_comando_fabricante.stdout.strip()

    digita_comando_modelo = subprocess.run(["adb", "shell", "getprop", "ro.product.model"], capture_output=True, text=True)
    dados["modelo"] = digita_comando_modelo.stdout.strip()

    digita_comando_versao = subprocess.run(["adb", "shell", "getprop", "ro.build.version.release"], capture_output=True, text=True)
    dados["versao_android"] = digita_comando_versao.stdout.strip()

    print(f"Serial Number:    {dados['serial_number']}")
    print(f"Fabricante:       {dados['fabricante']}")
    print(f"Modelo:           {dados['modelo']}")
    print(f"Versão do Android: {dados['versao_android']}")

def mostrar_dimensões():
    digita_comando = subprocess.run(["adb",
    "shell",
    "wm",
    "size"],capture_output=True,text=True)
    return digita_comando.stdout.strip()

def listar_apps():
    digita_comando = subprocess.run(["shell",
    "pm",
    "list",
    "packages"],capture_output=True,text=True)
    return digita_comando.stdout.strip()

def mostrar_activity():
    digita_comando = subprocess.run(["shell",
    "dumpsys",
    "window"],capture_output=True,text=True)
    return digita_comando.stdout.strip()

def abrir_camera():
    digita_comando = subprocess.run(["shell",
    "am",
    "start",
    "-a",
    "android.media.action.IMAGE_CAPTURE"],capture_output=True,text=True)
    return digita_comando.stdout.strip()

def voltar_home():
    digita_comando = subprocess.run(["shell",
    "input",
    "keyevent",
    "KEYCODE_HOME"], capture_output=True, text=True)
    return digita_comando.stdout.strip()

def verificar_stayAwake():
    digita_comando = subprocess.run(["shell",
    "settings",
    "get",
    "global",
    "stay_on_while_plugged_in"])
     #0 é o valor para desativado
    if digita_comando == 0:            
        digita_comando = subprocess.run([
        "shell",
        "settings",
        "put",
        "global",
        "stay_on_while_plugged_in",
        "3"
        ])
    return digita_comando.stdout.strip()

def verificar_modoAviao():
    digita_comando = subprocess.run(["shell",
    "settings",
    "get",
    "global",
    "airplane_mode_on"])

    if digita_comando == 1:
        print("Modo avião ativado.")
    else:
        print("Modo avião desativado.")

def tocar_meio():
    digita_comando = subprocess.run([ "shell",
    "input",
    "tap",
    "540",
    "1170"])

def swipe_topoBase():
    #dimensões do Samsung A15 (540,0) é o meio horizontal. 1000 é o tempo de swipe, medido em ms
    digita_comando = subprocess.run([ "shell",
    "input",
    "swipe",
    "540",
    "0",
    "540",
    "1920",
    "1000"])


