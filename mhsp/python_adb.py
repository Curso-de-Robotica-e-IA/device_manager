import subprocess
import time

PAIRING_CODE = "135806"
IP = "192.168.158.45"
PORT = "37579"


device_usb_code ="d36e54d8"
device_wifi_code = None #To be overriden


def _initial_setup():
    cmd = subprocess.run(["adb", "kill-server"], capture_output= True, text = True)
    cmd = subprocess.run(["adb", "start-server"], capture_output= True, text = True)


def get_devices():
    cmd = subprocess.run(["adb", "devices"], capture_output= True, text = True)
    return cmd.stdout


def get_connected_devices() -> list:
    """
    Returns a list of all devices that are CONNECTED.
    """
    cmd = get_devices()
    cmd = cmd.strip().strip('\t').split('\n')[1:]

    my_connected_devices = []
    for dvc in cmd:
        dvc = dvc.split('\t')
        if dvc[1] != "offline":
            my_connected_devices.append(dvc)

    return my_connected_devices


def pair_device(ip, port, code):
    try:
        print("Trying to pair device via code...")
        cmd = subprocess.run(["adb", "pair", f"{ip}:{port}", f"{code}"], capture_output= True, text = True)
    except Exception as e:
        print(e)


def connect_device_wifi(ip, port):
    cmd = subprocess.run(["adb", "connect", f"{ip}:{port}"], capture_output= True, text = True)
    print(f'O resultado do comando de connect via wifi foi: {cmd.stdout}')
    try:
        device_wifi_code = cmd.stdout.strip().split()[2]

        extracted_port = device_wifi_code.split(":")[1]
        extracted_ip = device_wifi_code.split(":")[0]

        print(f'Device wifi code : {device_wifi_code}')
        print(f'IP : {extracted_ip}')
        print(f'PORT: {extracted_port}')
    except Exception as e:
        print(e)



def check_screen_on():
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "dumpsys", "deviceidle ", "|", " grep", "'mScreenOn'"], capture_output= True, text = True)
    state = None
    try:
        state = cmd.stdout.strip().split('=')[1]
        if state == "false":
            print("Screen is off! Turning it on...")
            cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "input", "keyevent ", "KEYCODE_WAKEUP"], capture_output= True, text = True)
        else:
            print("Screen was already on...")
    except Exception as e:
        print(e)
    return state


def check_screen_block():
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "dumpsys", "deviceidle ", "|", " grep", "'mScreenOn'"], capture_output= True, text = True)
    state = None
    try:
        state = cmd.stdout.strip().split('=')[1]
        if state == "false":
            print("Screen was locked. Unlocking it...")
            cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "input", "keyevent ", "KEYCODE_WAKEUP"], capture_output= True, text = True)
        else:
            print("Screen was already unlocked.")
    except Exception as e:
        print(e)


def show_device_info():
    #serial number : 'ro.serialno'
    #fabricante : 'ro.product.manufacturer'
    #modelo : 'ro.product.model'
    #versao OS : 'ro.build.version.release'

    cmd_sn = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "getprop", "ro.serialno"], capture_output= True, text = True)
    cmd_manufacturer = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "getprop", "ro.product.manufacturer"], capture_output= True, text = True)
    cmd_model = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "getprop", "ro.product.model"], capture_output= True, text = True)
    cmd_os_version = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "getprop", "ro.build.version.release"], capture_output= True, text = True)

    print(f"Serial number : {cmd_sn.stdout}")
    print(f"Manufacturer : {cmd_manufacturer.stdout}")
    print(f"Model : {cmd_model.stdout}")
    print(f"Version : {cmd_os_version.stdout}")


def get_device_dimensions():
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "wm", "size"], capture_output= True, text = True)
    print(f"Dimensoes da tela  : {cmd.stdout}")
    return cmd.stdout


def get_installed_apps():
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "pm", "list", "packages"], capture_output= True, text = True)
    print(f"Installed packages :\n {cmd.stdout}")
    return cmd.stdout


def show_task_name():
    #adb -s d36e54d8 shell "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'"  
    print("SHOWING TASK NAME")
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "dumpsys", "window", "|", "grep", "-E", "'mCurrentFocus|mFocusedApp'"], capture_output= True, text = True)
    print(cmd)
    print(f'Current task name : {cmd.stdout}')


def open_camera():
    print("Opening camera")
    time.sleep(2)
    #adb -s d36e54d8 shell am start -n com.android.camera/.Camera
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "am", "start ", "-n", "com.android.camera/.Camera"], capture_output= True, text = True)



def go_to_home():
    print("Going to home")
    time.sleep(2)
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "input", "keyevent ", "3"], capture_output= True, text = True)


def check_stay_awake():
    #adb -s d36e54d8 shell settings get global stay_on_while_plugged_in   
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "settings", "get ", "global", "stay_on_while_plugged_in"], capture_output= True, text = True)
    if cmd.stdout.strip() == "0":
        print("Modo stay awake está desativado. Ativando-o...")
        #adb -s d36e54d8 shell settings put global stay_on_while_plugged_in 3
        cmd1 = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "settings", "put ", "global", "stay_on_while_plugged_in", "3"], capture_output= True, text = True)
    else:
        print("Modo stay awake está ativado.")
    


def check_airplane_mode():
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "settings", "get ", "global", "airplane_mode_on"], capture_output= True, text = True)
    if cmd.stdout.strip() == '1':
        print("Airplane mode is enabled")
        return True
    else:
        print("Airplane mode is disabled")
        return False

def touch_screen():
    #adb -s d36e54d8 shell input tap 540 1200  
    print("Touching screen in the middle")
    time.sleep(2)
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "input", "tap", "540", "1200"], capture_output= True, text = True)
    

def swipe_screen():
    time.sleep(2)
    #Faz um swipe do topo da tela (x = "meio", y = 0) até o final (x = "meio", y = 2300)
    print("Screen swipping...")
    cmd = subprocess.run(["adb", "-s", f"{device_usb_code}", "shell", "input", "swipe", "500", "0", "500", "2300", "3000"], capture_output= True, text = True)
    #print(cmd.stdout)
    


_initial_setup()

print(f'Current devices : {get_devices()}')


# pair_device(IP, PORT, PAIRING_CODE) #Remove comment to use it.
# connect_device_wifi(IP, PORT) #Remove comment to use it.

print(f'Connected devices : {get_connected_devices()}')

print(f"Checking if screen state : {check_screen_on()}")
print(f"checking screen lock state : {check_screen_block()}")

show_device_info()
get_device_dimensions()
get_installed_apps()
show_task_name()

time.sleep(2)
open_camera()
time.sleep(2)
go_to_home()
check_stay_awake() 
check_airplane_mode()
touch_screen() #Touches the middle of the screen
swipe_screen()
