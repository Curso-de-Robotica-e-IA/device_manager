from connection.device_connection import ConnectionManager


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
