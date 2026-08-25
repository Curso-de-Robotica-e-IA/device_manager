import subprocess


IP_address_port = "192.168.158.29:45773 757939"
device_IP = "192.168.158.29:38685" 

def list_of_devices():  #1
	r = subprocess.run(
		["adb", "devices", "-l"], capture_output=True,
		text=True,
	)
	return r.stdout


def pair_device(IP_address_port):           #2
	r_pair = subprocess.run( ["adb", "pair", IP_address_port.split()[0]], input=IP_address_port.split()[1] + "\n", capture_output=True, text=True,
	)
	return r_pair.stdout or r_pair.stderr


def connect_device(device_IP):
	r_connect = subprocess.run(["adb", "connect", device_IP], capture_output=True, text=True)
	return r_connect.stdout or r_connect.stderr


def connect_device_sn(device_IP):        #3
    r_sn = subprocess.run(["adb", "-s", device_IP, "get-state"], capture_output = True, text = True
	)
    return r_sn.stdout or r_sn.stderr

def show_devices():  #4
	r_show = subprocess.run(["adb", "devices"], capture_output=True, text=True)
	return r_show.stdout


def screen_is_on(device_IP):
    screen_res = subprocess.run(
        ["adb", "-s", device_IP, "shell", "dumpsys", "power"],
        capture_output=True,
        text=True,
    )
    output = screen_res.stdout.lower()

    if "mwakefulness=awake" in output or "display power: state=on" in output:
        print("The screen is on")
        return True

    print("The screen is off. Turning it on...")
    subprocess.run(
        ["adb", "-s", device_IP, "shell", "input", "keyevent", "26"],
        capture_output=True,
        text=True,
    )
    return True


def screen_is_locked(device_IP):
    r_locked = subprocess.run(
        ["adb", "-s", device_IP, "shell", "dumpsys", "window", "policy"],
        capture_output=True,
        text=True,
    )
    output = r_locked.stdout.lower()

    if "keyguard" in output or "mdreaminglockscreen=true" in output:
        return True

    return False


def unlock_screen(device_IP):
    if screen_is_locked(device_IP):
        print("The screen is locked. Unlocking...")
        screen_is_on(device_IP)
        subprocess.run(
            ["adb", "-s", device_IP, "shell", "input", "swipe", "300", "1500", "300", "300"],
            capture_output=True,
            text=True,
        )
        print("Unlocked Screen")
    else:
        print("The screen is already unlocked")

def show_device_info(device_IP): 
    subprocess.run(["adb", "-s", device_IP, "shell", "getprop", "ro.serialno"])
    subprocess.run(["adb", "-s", device_IP, "shell", "getprop", "ro.product.manufacturer"])
    subprocess.run(["adb", "-s", device_IP, "shell", "getprop", "ro.product.model"])
    subprocess.run(["adb", "-s", device_IP, "shell", "getprop", "ro.build.version.release"])
 

print(list_of_devices())
print(pair_device(IP_address_port))
print(connect_device(device_IP))
print(show_devices())
print(screen_is_on(device_IP))
print(screen_is_locked(device_IP))
unlock_screen(device_IP)
show_device_info(device_IP)










