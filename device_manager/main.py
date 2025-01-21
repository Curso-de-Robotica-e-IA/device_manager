from connection.device_connection import DeviceConnection


def main():
    cm = DeviceConnection()
    serial_numbers = cm.prompt_device_connection()
    deu_bom = cm.start_connection(serial_numbers)
    print(deu_bom)


if __name__ == '__main__':
    main()
