import enum
from enum import Enum

class LabelMode(Enum):
    DEFAULT_MODE = enum.auto()
    POINT_MODE = enum.auto()
    LINE_MODE = enum.auto()
    ANGLE_MODE = enum.auto()
    CIRCLE_MODE = enum.auto()
    MIDPOINT_MODE = enum.auto()
    VERTICAL_MODE = enum.auto()
    MOVE_POINT_MODE = enum.auto()
    ERASE_POINT_MODE = enum.auto()
