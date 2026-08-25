from device_manager import DeviceManager
from device_manager.connection.adb_pairing import AdbPairing

def listar_dispositivos():
    manager = DeviceManager()
    network_devices = manager.connector.visible_devices()
    print(f"Dispositivos disponíveis: {network_devices}")

def emparelhar_dispositivo():
    
    pairing_server = AdbPairing()
    pairing_server.start()  

    print("Dados para o QR Code:", pairing_server.qrcode_string) 
    success = pairing_server.pair_devices()  
    pairing_server.stop_pair_listener()

def conectar_serial_number(serial_number):
    manager = DeviceManager()
    device = manager.connector.start_connection(serial_number)
    if device:
        print(f"Conectado ao dispositivo com serial number: {serial_number}")
    else:
        print(f"Falha ao conectar ao dispositivo com serial number: {serial_number}")

if __name__ == "__main__":
    listar_dispositivos()
    emparelhar_dispositivo()
    conectar_serial_number("e8fbf133") 
