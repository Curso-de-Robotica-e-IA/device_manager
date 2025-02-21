import secrets
import string
import subprocess
from weakref import finalize
import cv2 as cv
import numpy as np
import qrcode
from zeroconf import ServiceBrowser, Zeroconf
from device_manager.connection.utils.mdns_context import MDnsContext
from device_manager.connection.utils.mdns_listener import MDnsListener


class AdbPairing:
    def __init__(self):
        self.__name = "robot-celular"
        self.__qr = None
        self.__qr_image = None
        self.__passwd = self.__create_password()
        self.__qrcode()
        self.__service_re_filter = None
        self.__service_type = "_adb-tls-pairing._tcp.local."
        self.__zeroconf = None
        self.__context = MDnsContext()
        self.__started = False
        self.__browser = None
        self.__finalize = None

    @staticmethod
    def __create_password():
        alphabet = string.ascii_letters + string.digits

        return "".join(secrets.choice(alphabet) for i in range(8))

    def __qrcode(self):
        s = f"WIFI:T:ADB;S:{self.__name};P:{self.__passwd};;"
        self.__qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=20,
            border=2,
        )
        self.__qr.add_data(s)
        self.__qr_image = self.__qr.make_image(
            fill_color="black",
            back_color="white",
        )

    def start(self):
        if not self.__started:
            self.__zeroconf = Zeroconf()
            self.__browser = ServiceBrowser(
                self.__zeroconf,
                self.__service_type,
                MDnsListener(
                    self.__context,
                    self.__service_re_filter,
                    self.__service_type,
                ),
            )

            def atexit(zeroconf):
                zeroconf.close()
            self.__finalize = finalize(
                self.__zeroconf,
                atexit,
                self.__zeroconf,
                )
            self.__started = True

    def qrcode_prompt_show(self):
        self.__qr.print_ascii(tty=True)

    def qrcode_cv_window_show(self):
        cv.imshow("pair", self.__get_img_cv())
        cv.waitKey(0)
        cv.destroyAllWindows()

    def __get_img_cv(self):
        img_rgb = self.__qr_image.convert("RGB")
        img_mat = cv.cvtColor(np.array(img_rgb), cv.COLOR_RGB2BGR)

        return cv.resize(img_mat, (400, 400))

    def has_device_to_pairing(self):

        return len(self.__context.get_online_service()) > 0

    def pair_devices(self):
        success = False
        online_services = self.__context.get_online_service()
        for elem in online_services.items():
            comm_uri = f"{elem[1].ip}:{elem[1].port}"
            result = subprocess.run(
                ["adb", "pair", comm_uri, self.__passwd],
                capture_output=True,
                text=True,
            )
            if f"Successfully paired to {comm_uri}" in result.stdout:
                success = True

        return success

    def stop_pair_listener(self):
        self.__zeroconf.close()
