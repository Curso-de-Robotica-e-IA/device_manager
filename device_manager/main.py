from connection.device_connection import DeviceConnection


def main():
    cm = DeviceConnection()
    cm.start_connection()


if __name__ == '__main__':
    main()
