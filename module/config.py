class Config(object):
    def __init__(self):
        # Font Size
        self.fontSize = 10
        # Font Family
        self.fontFamily = 'Consolas'
        # Shifting
        self.indexShifting = 3
        self.distanceShifting = 8
        self.degreeShiftingBase = 15
        self.degreeShiftingMore = 30
        # Width
        self.pointWidth = 7
        self.lineWidth = 3
        self.angleWidth = 2
        # Color
        self.defaultColor = 'red'
        self.colorList = ('red', 'green', 'blue', 'cyan', 'yellow', 'black', 'white', 'gray')
        # Action
        self.defaultAction = '无操作'
        self.actionList = ('无操作', '点', '线', '角度', '圆', '中点', '直角', '移动点', '删除点')
        # Indent
        # For JSON
        self.indent = 2
        # Ratio
        # For ∠ABC, the radius of the degree is r = min(AB, AC) * ratioToRadius
        self.ratioToRadius = 0.2
        # Math Constant
        self.eps = 1e-5
        self.base = 2 ** 7

    def __getattr__(self, item):
        if item in self.__dict__:
            return self.item
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def __setattr__(self, key, value):
        if key in self.__dict__:
            raise AttributeError("can't set attribute")
        self.__dict__[key] = value

config = Config()
