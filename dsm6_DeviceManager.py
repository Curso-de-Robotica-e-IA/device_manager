import time
from device_manager import DeviceManager, DeviceInfo, DeviceActions
from device_manager.connection.adb_pairing import AdbPairing

serial = 'RX8Y3014GAX'
manager = DeviceManager()
scout, actioner = manager[serial]

def mostrar_dispositivos():

    dispositivos_usb = manager.connected_devices

    print("Dispositivos USB detectados:")    
    print(dispositivos_usb)

def parear_manual():
    pareador = AdbPairing(subprocess_check_flag=True)
        
    ip_porta = "172.22.68.190:41523"         # Esse IP e porta aparecem na tela de depuração wifi do dispositivo, na opção que diz para parear com código
    codigo_pin = "531810"                      # Substitua pelo seu Número de 6 dígitos
        
    print(f"Tentando parear com {ip_porta}...")
        

    sucesso = pareador.pair_device_with_paring_code(
        comm_uri=ip_porta, 
        pair_code=codigo_pin
    )

    # 4. Verifica o resultado
    if sucesso:
        print("Dispositivo pareado com sucesso!")
    else:
        print("Falha no pareamento. Verifique se o IP/Porta ou PIN estão corretos.")

    manager = DeviceManager()

    manager.connect_devices("172.22.68.190:37673") #Esse IP aparece na tela de depuração wifi, logo abaixo do nome do dispositivo

def listar_dispositivos():
        
    dispositivos = manager.connector.visible_devices()
    print("Dispositivos USB/WIFI detectados:")
    for dev in dispositivos:
            
            serial = dev.serial_number
            tipo = dev.connection.name if hasattr(dev.connection, 'name') else str(dev.connection)
            
            print(f"{serial:<30} | {tipo:<15}")



def ligar_tela():

    conectados = manager.connect_devices(serial)
    print(f"Dispositivos conectados com sucesso: {conectados}")

    if serial in conectados:
        scout, actioner = manager[serial]
        
        if not scout.is_screen_on:
            print("Ligando a tela...")
            actioner.turn_on_screen()
        else:
            print("Tela já está ligada.")
    else:
        print(f"O dispositivo {serial} não pôde ser conectado pelo ADB.")


def desbloquear_tela_sem_pin():
    conectados = manager.connect_devices(serial)
    print(f"Dispositivos conectados com sucesso: {conectados}")
    if serial in conectados:
            actioner.turn_on_screen()        
            if scout.is_device_locked:
                print("Desbloqueando dispositivo")
                actioner.unlock_screen()
            else:
                print("Tela já está desbloqueada.")

#def desbloquear_tela_com_pin():
     

def recuperar_info():
    propriedades = scout.get_properties()

    if isinstance(propriedades, dict):
        fabricante = propriedades.get('brand', 'Não encontrado')
        modelo = propriedades.get('model', 'Não encontrado')
        versao_android = propriedades.get('android_version', 'Não encontrado')
    
    print(f"Serial Number:  {scout.serial_number}")
    print(f"Fabricante:     {fabricante.upper()}")
    print(f"Modelo:         {modelo.upper()}")
    print(f"Versão Android: Android {versao_android}")

def mostrar_dimensões():
        print(scout.get_screen_dimensions())

def listar_apps():
     print (scout.list_installed_all_apps())

def mostrar_activity():
     print (scout.actual_activity())

def abrir_camera():
    pacote_camera = "com.sec.android.app.camera"

    conectados = manager.connect_devices(serial)
    
    if serial not in conectados:
        print(f"Não foi possível conectar ao dispositivo {serial}.")
        return
        
    scout, actioner = manager[serial]
    
    
    if not scout.is_screen_on:
        actioner.turn_on_screen()
        time.sleep(0.5)
        
    if scout.is_device_locked:
        print("O dispositivo está bloqueado. Desbloqueie o aparelho primeiro para abrir o app.")
        return

    print("Iniciando o aplicativo da Câmera...")


    if hasattr(actioner, 'start_app'):
        actioner.start_app(pacote_camera)
        print("Comando enviado via actioner.start_app()")
        
    elif hasattr(actioner, 'launch_app'):
        actioner.launch_app(pacote_camera)
        print("Comando enviado via actioner.launch_app()")

def home_button():
      return actioner.home_button()

def awake_ativado():
     return scout.is_stay_awake_enabled()

def checar_modo_aviao():
     return scout.is_airplane_mode_enabled()

def toque_meio():
     return actioner.click_by_coordinates(540,585)

def realizar_swipe():
     return actioner.swipe(540,0,540,1920,1000)


