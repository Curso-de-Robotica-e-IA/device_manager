from device_manager import DeviceManager, AdbPairing


DEVICE_IP_PORTA = "192.168.155.62:38259"
CODE = "497892"
SERIAL_NUMBER_MOTO_EDGE_30 = "0083078983"


def executar_tudo_dm():
    manager = DeviceManager()  

    try:
        device_info, device_action = manager[SERIAL_NUMBER_MOTO_EDGE_30]  

        # 01 Mostrar os devices disponíveis
        print("#01. Mostrar os devices disponíveis")
        for d in manager.connector.visible_devices():
             print(d)
        

        # 02 Parear device utilizando o Código de pareamento
        print("#02. Parear device utilizando o Código de pareamento")
        pair_ip = AdbPairing()
        if pair_ip.pair_device_with_paring_code(DEVICE_IP_PORTA, CODE):
             print(f"Dispositivo conectado no IP/Porta:{DEVICE_IP_PORTA} e Código:{CODE}")

        # 03 Conectar device pelo serial number
        print("#03. Conectar device pelo serial number")
        manager.connect_devices(
            SERIAL_NUMBER_MOTO_EDGE_30)
        print(f"Dispositivo conectado com o Serial Number {SERIAL_NUMBER_MOTO_EDGE_30}")

        # 04 Mostrar devices conectados via usb e via wifi
        print("#04. Mostrar devices conectados via USB e via Wi-Fi")
        devices = manager.connector.visible_devices()
        for device in devices:
             print(device)
        
        # 05 Verificar se a tela está ligada
        print("#05. Verificar se a tela está ligada")
        # 06 Ligar caso desligada
        print("#06. Ligar caso desligada")

        if device_info.is_screen_on():
            print("A tela já tá ligada!")
        else:
            print("Tela desligada!!!   Ligando a tela...")
            manager.execute_adb_command(
            'input keyevent 26',
            comm_uris=[SERIAL_NUMBER_MOTO_EDGE_30],
        ) 

        # 07 Verificar se a tela está bloqueada
        print("#07. Verificar se a tela está bloqueada")
        # # 08 Desbloquear caso bloqueada
        print("#08. Desbloquear caso bloqueada")

        if device_info.is_device_locked():
            print("A tela está bloqueada! Desbloqueando...")
            manager.execute_adb_command(
                'input keyevent 82',
                comm_uris=[SERIAL_NUMBER_MOTO_EDGE_30],
            ) 
        else:
            print("A tela já está desbloqueada!")


        # 09 Mostrar o serial_number, fabricante, modelo e versão do android
        print("#09. Mostrar serial, fabricante, modelo e versão do Android")
        print(device_info.get_properties())

        # 10 Mostrar as dimensões da tela
        print("#10. Mostrar as dimensões da tela")
        print(device_info.get_screen_dimensions())

        # 11 Listar todos os apps instalados
        print("#11. Listar todos os apps instalados")
        print(device_info.list_installed_all_apps())

        # 12 Mostrar o nome da activity atual
        print("#12. Mostrar o nome da activity atual")
        print(device_info.actual_activity())

        # 13 Abrir a câmera pelo package e activity
        print("#13. Abrir a câmera")
        manager.execute_adb_command(
                'input keyevent 27',
                comm_uris=[SERIAL_NUMBER_MOTO_EDGE_30],
        ) 

        # 14 Ir para o home
        print("#14. Ir para o home")
        manager.execute_adb_command(
                'input keyevent 3',
                comm_uris=[SERIAL_NUMBER_MOTO_EDGE_30],
        ) 

        # 15 Verificar se o stay awake está ativado
        print("#15. Verificar se o stay awake está ativado")
        # # 16 Ativar caso desativado
        print("#16. Ativar stay awake")
        if device_info.is_stay_awake_enabled():
            print(f"Valor atual do Stay Awake: {device_info.is_stay_awake_enabled()}")
        else:
            print("Stay awake desativado! Ativando...")
            manager.execute_adb_command(f"shell settings put global stay_on_while_plugged_in 3", shell=True)

        # 17 Verificar se o modo avião está ativado
        print("#17. Verificar se o modo avião está ativado")
        if device_info.is_airplane_mode_enabled():
            print("Modo avião ligado!")
        else:
            print("Modo avião desligado!")

        # 18 Realizar uma ação de toque no meio da tela
        print("#18. Realizar toque no meio da tela")
        manager.execute_adb_command(f"input tap 540 1200")

        # 19 Realizar um swipe do topo até a base da tela
        print("#19. Realizar swipe do topo até a base")
        manager.execute_adb_command(f"input swipe 500 200 500 1800 500")

    except Exception as erro:
            print(f"Ocorreu um erro do tipo: {erro}")


executar_tudo_dm()            