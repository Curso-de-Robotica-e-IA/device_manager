import subprocess, shlex



class ManagerDevice:
    IP = "192.168.158.27:"
    def execute_adb_devices():
        subprocess.run(["adb", "devices"])
        
        
    def execute_adb_pair_ip():
        ManagerDevice.IP
        lista = ["adb", "pair"]
        ManagerDevice.IP = f"{ManagerDevice.IP}{input("Digite ip:port -> ")}"
        lista.append(ManagerDevice.IP)
        subprocess.run(lista)

    def execute_adb_connect_port():
        lista = ["adb", "connect"]
        ManagerDevice.IP = f"{ManagerDevice.IP}{input("Digite ip:port -> ")}"
        lista.append(ManagerDevice.IP)
        subprocess.run(lista)


if __name__ == "__main__":
    ...
