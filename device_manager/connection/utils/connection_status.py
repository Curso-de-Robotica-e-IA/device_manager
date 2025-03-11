from enum import Enum, auto


class ConnectionInfoStatus(Enum):
    UPDATED = auto()
    CHANGED = auto()
    DOWN = auto()
    UNKNOWN = auto()
