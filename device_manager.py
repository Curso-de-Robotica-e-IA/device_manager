import os
import re
import subprocess
from time import sleep
from xml.etree import ElementTree
import uiautomator2 as u2

from device.connection.device_connection import ConnectionManager


class Devices:
    def __init__(self):
        self.connection_info = None
        self.screen_width = None
        self.screen_width_half = None
        self.screen_height = None
        self.screen_height_half = None
        self.connection_manager = ConnectionManager()
        self.current_comm_uri = None
        self.model = None
