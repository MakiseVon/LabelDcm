from module.mode import LabelMode
from typing import Any


class ModeNameDict(dict):
    def __init__(self):
        super().__init__()
        self[LabelMode.DEFAULT_MODE] = '无'
        self[LabelMode.POINT_MODE] = '点'
        self[LabelMode.LINE_MODE] = '线'
        self[LabelMode.ANGLE_MODE] = '角'
        self[LabelMode.CIRCLE_MODE] = '圆'
        self[LabelMode.MIDPOINT_MODE] = '中点'
        self[LabelMode.VERTICAL_MODE] = '直角'
        self[LabelMode.MOVE_POINT_MODE] = '移动点'
        self[LabelMode.ERASE_POINT_MODE] = '删除点'


class Config:
    def __init__(self):
        # font size
        self.font_size = 10

        # font family
        self.font_family = 'Consolas'

        # shifting
        self.index_shifting = 3
        self.distance_shifting = 8
        self.degree_shifting_base = 15
        self.degree_shifting_more = 30

        # width
        self.point_width = 7
        self.line_width = 3
        self.angle_width = 2

        # color
        self.default_color = 'red'
        self.color_list = ('red', 'green', 'blue', 'cyan', 'yellow', 'black', 'white', 'gray')

        # action
        self.default_action_mode = LabelMode.DEFAULT_MODE
        self.action_mode_list = (
            LabelMode.DEFAULT_MODE, LabelMode.POINT_MODE, LabelMode.LINE_MODE, LabelMode.ANGLE_MODE,
            LabelMode.CIRCLE_MODE, LabelMode.MIDPOINT_MODE, LabelMode.VERTICAL_MODE, LabelMode.MOVE_POINT_MODE,
            LabelMode.ERASE_POINT_MODE
        )
        self.action_name_list = ('无', '点', '线', '角', '圆', '中点', '直角', '移动点', '删除点')

        # indent
        # for JSON
        self.indent = 2

        # ratio
        # for ∠abc, the radius of the degree is r = min(ab, ac) * ratio_to_radius
        self.ratio_to_radius = 0.2

        # math constant
        self.eps = 1e-5
        self.base = 2 ** 7

    def __getattr__(self, key: str):
        if key in self.__dict__:
            return self.__dict__[key]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{key}'.")

    def __setattr__(self, key: str, value: Any):
        if key in self.__dict__:
            raise AttributeError("can't set attribute.")
        self.__dict__[key] = value


config = Config()
