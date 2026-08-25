import subprocess


    def list_devices():
        return 
        

#     def list_of_devices(self):
#         try:
#             r = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True, check=True)
#             return r.stdout
#         except FileNotFoundError:
#             print("Erro: ADB NOT FOUND on PATH.")
#             return ""
#         except subprocess.CalledProcessError as error:
#             print(f"Error executing ADB: {error.stderr}")
#             return ""


# def pair_device(address, pairing_code):
#     r = subprocess.run(
#         ["adb", "pair", address],
#         input=f"{pairing_code}\n",
#         capture_output=True,
#         text=True,
#     )
#     return r.stdout or r.stderr


# def connect_device_sn(serial_number):
#     r = subprocess.run(
#         ["adb", "-s", serial_number, "get-state"],
#         capture_output=True,
#         text=True,
#     )
#     return r.stdout or r.stderr


# def show_devices():
#     r = subprocess.run(["adb", "devices"], capture_output=True, text=True)
#     return r.stdout


# def screen_is_on(serial_number):
#     r = subprocess.run(
#         ["adb", "-s", serial_number, "shell", "dumpsys", "power"],
#         capture_output=True,
#         text=True,
#     )
#     return "mWakefulness=Awake" in r.stdout or "Display Power: state=ON" in r.stdout


# def list_of_devices():
#     try:
#         r = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True, check=True)
#         output = r.stdout
#         device_lines = [line for line in output.splitlines()[1:] if line.strip()]
#         if not device_lines:
#             print("Nenhum dispositivo detectado. Ative a depuracao USB e autorize este computador no celular.")
#         return output
#     except FileNotFoundError:
#         print("Erro: ADB NOT FOUND on PATH.")
#         return ""
#     except subprocess.CalledProcessError as error:
#         print(f"Error executing ADB: {error.stderr}")
#         return ""


# # comando manual: IP:porta | código

# def pair_devices(ip: str, port: str, code: str):
#     cmd = ["adb", "pair", f"{ip}:{port}", code]

#     try:
#         res1 = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
#         print("ADB output: ", res1.stdout.strip())
#         return "The device is connected successfully" in res1.stdout
#     except subprocess.CalledProcessError as error:
#         print(f"Pairing Error {error.stderr.strip()}")
#         return False
#     except FileNotFoundError:
#         print("Erro: ADB NOT FOUND on PATH.")
#         return False


# if __name__ == "__main__":
#     print(list_of_devices())
#     print(screen_is_on("SERIAL_DO_DEVICE"))
