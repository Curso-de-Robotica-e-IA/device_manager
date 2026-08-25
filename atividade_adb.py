import subprocess


DEVICE_IP_PORTA_CODE = "192.168.155.62:42909 574301"
DEVICE_IP_PORTA = "192.168.155.62:37859"

def executar_tudo_adb():
    try:
        # 01 Mostrar os devices disponíveis
        print("#01. Mostrar os devices disponíveis")
        subprocess.run("adb devices -l", shell=True)

        # 02 Parear device utilizando o Código de pareamento
        print("#02. Parear device utilizando o Código de pareamento")
        subprocess.run(f"adb pair {DEVICE_IP_PORTA_CODE}", shell=True)

        # 03 Conectar device com IP e Porta
        print("#03. Conectar device com IP e Porta")
        subprocess.run(f"adb connect {DEVICE_IP_PORTA}", shell=True)

        # 04 Mostrar devices conectados via USB e via Wi-Fi
        print("#04. Mostrar devices conectados via USB e via Wi-Fi")
        subprocess.run("adb devices", shell=True)
        
        # 05 Verificar se a tela está ligada
        print("#05. Verificar se a tela está ligada")
        # 06 Ligar caso desligada
        print("#06. Ligar caso desligada")

        resultado_tela = subprocess.run(
            f"adb -s {DEVICE_IP_PORTA} shell dumpsys display", 
            shell=True, capture_output=True, text=True
        )
        if "mDisplayState=OFF" in resultado_tela.stdout or "state=OFF" in resultado_tela.stdout:
            print("Tela está desligada! Ligando...")
            subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell input keyevent 26", shell=True)
        else:
            print("a tela já tá ligada!")

        # 07 Verificar se a tela está bloqueada
        print("#07. Verificar se a tela está bloqueada")
        # # 08 Desbloquear caso bloqueada
        print("#08. Desbloquear caso bloqueada")
        resultado_trava = subprocess.run(
            f"adb -s {DEVICE_IP_PORTA} shell dumpsys trust", 
            shell=True, capture_output=True, text=True
        )
        if "mIsActive=false" in resultado_trava.stdout or "mUnlocked=false" in resultado_trava.stdout:
            print("A tela está bloqueada! Desbloqueando...")
            subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell input keyevent 82", shell=True)
        else:
            print("A tela já está desbloqueada!")

        # 09 Mostrar o serial_number, fabricante, modelo e versão do android
        print("#09. Mostrar serial, fabricante, modelo e versão do Android")
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell getprop ro.serialno", shell=True)
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell getprop ro.product.manufacturer", shell=True)
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell getprop ro.product.model", shell=True)
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell getprop ro.build.version.release", shell=True)

        # 10 Mostrar as dimensões da tela
        print("#10. Mostrar as dimensões da tela")
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell wm size", shell=True)

        # 11 Listar todos os apps instalados
        print("#11. Listar todos os apps instalados")
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell pm list packages", shell=True)

        # 12 Mostrar o nome da activity atual
        print("#12. Mostrar o nome da activity atual")
        subprocess.run(f'adb -s {DEVICE_IP_PORTA} shell "dumpsys window | grep -E \'mCurrentFocus|mFocusedApp\'"', shell=True)

        # 13 Abrir a câmera pelo package e activity
        print("#13. Abrir a câmera")
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell am start -a android.media.action.STILL_IMAGE_CAMERA", shell=True)

        # 14 Ir para o home
        print("#14. Ir para o home")
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell input keyevent 3", shell=True)

        # 15 Verificar se o stay awake está ativado
        print("#15. Verificar se o stay awake está ativado")
        # # 16 Ativar caso desativado
        print("#16. Ativar stay awake")
        resultado_awake = subprocess.run(
            f"adb -s {DEVICE_IP_PORTA} shell settings get global stay_on_while_plugged_in", 
            shell=True, capture_output=True, text=True
        )
        valor_awake = resultado_awake.stdout.strip()
        print(f"Valor atual do Stay Awake: {valor_awake}")

        if valor_awake != "3":
            print("Stay awake desativado! Ativando...")
            subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell settings put global stay_on_while_plugged_in 3", shell=True)
        else:
            print("Stay awake já tá ativado!")

        # 17 Verificar se o modo avião está ativado
        print("#17. Verificar se o modo avião está ativado")
        resultado_aviao = subprocess.run(
            f"adb -s {DEVICE_IP_PORTA} shell settings get global airplane_mode_on", 
            shell=True, capture_output=True, text=True
        )
        modo_aviao_valor = resultado_aviao.stdout.strip()
        if modo_aviao_valor == "1":
            print("Modo avião está LIGADO!")
        else:
            print("Modo avião está DESLIGADO!")

        # 18 Realizar uma ação de toque no meio da tela
        print("#18. Realizar toque no meio da tela")
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell input tap 540 1200", shell=True)

        # 19 Realizar um swipe do topo até a base da tela
        print("#19. Realizar swipe do topo até a base")
        subprocess.run(f"adb -s {DEVICE_IP_PORTA} shell input swipe 500 200 500 1800 500", shell=True)

    except Exception as erro:
        print(f"Ocorreu um erro do tipo: {erro}")


executar_tudo_adb()