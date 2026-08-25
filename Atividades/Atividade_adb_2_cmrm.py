import subprocess


IP_address_port = "192.168.158.29:45773 757939"
device_IP = "192.168.158.29:38685" 


def show_screen_size(device_IP):  # 10
    subprocess.run(["adb", "-s", device_IP, "shell", "wm", "size"], shell=True)


def list_apps(device_IP):  # 11
    subprocess.run(["adb", "-s", device_IP, "shell",  "pm", "list", "packages"], shell=True)


def show_current_activity(device_IP):  # 12
    subprocess.run(
        f'adb -s {device_IP} shell "dumpsys window | grep -E \'mCurrentFocus|mFocusedApp\'"',
        shell=True,
    )


def open_camera(device_IP):  # 13
    subprocess.run(["adb", "-s", device_IP, "shell", "am", "start", "-a", "android.media.action.STILL_IMAGE_CAMERA"],
        shell=True,
    )


def go_to_home(device_IP):  # 14
    subprocess.run(["adb", "-s", device_IP, "shell", "input", "keyevent", "3"], shell=True)


def check_stay_awake(device_IP):  # 15
    r = subprocess.run(["adb", "-s", device_IP, "shell", "settings", "get", "global", "stay_on_while_plugged_in"],
        shell=True,
        capture_output=True,
        text=True,
    )
    print(r.stdout.strip())


def enable_stay_awake(device_IP):  # 16
    subprocess.run(
        ["adb", "-s", device_IP, "shell", "settings", "put",  "global", "stay_on_while_plugged_in", "3"],
        shell=True,
    )


def check_airplane_mode(device_IP):  # 17
    r = subprocess.run(
        ["adb", "-s", device_IP, "shell", "settings",  "get", "global", "airplane_mode_on"],
        shell=True,
        capture_output=True,
        text=True,
    )
    print(r.stdout.strip())


def tap_screen(device_IP):  # 18

    subprocess.run(["adb", "-s", device_IP, "shell", "input", "tap", "540", "1200"], shell=True)


def swipe_screen(device_IP):  # 19
    subprocess.run(
        ["adb", "-s", device_IP, "shell", "input", "swipe", "500", "200", "500", "1800", "500"],
        shell=True,
    )


show_screen_size(device_IP)
list_apps(device_IP)
show_current_activity(device_IP)
open_camera(device_IP)
# go_to_home(device_IP)
# check_stay_awake(device_IP)
# enable_stay_awake(device_IP)
# check_airplane_mode(device_IP)
# tap_screen(device_IP)
# swipe_screen(device_IP)


