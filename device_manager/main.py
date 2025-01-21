from connection.device_connection import DeviceConnection


def main():
    cm = DeviceConnection()
    deu_bom = cm.start_connection()
    print(deu_bom)


if __name__ == '__main__':
    main()
