import json
import math
from module.config import config
import numpy
import os
from PIL import Image
from pydicom import dcmread, FileDataset
from pydicom.dicomdir import DicomDir
from PyQt5.QtCore import QPointF, QRectF
from typing import Optional, Union

def is_file_exists(path: str):
    return os.path.exists(path)

def is_file_readable(path: str):
    return os.access(path, os.R_OK)

def is_file_writable(path: str):
    return os.access(path, os.W_OK)

def get_attr(dcm: Union[FileDataset, DicomDir], name: str):
    attr = getattr(dcm, name, None)
    if attr is not None:
        attr = str(attr).strip(' \t\n\r')
    return attr if attr else None

def to_date(date: Optional[str]):
    return date[0:4] + '年' + date[4:6] + '月' + date[6:8] + '日' if date else None

def to_sex(sex: Optional[str]):
    if not sex:
        return None
    sex = sex.lower()
    if sex == 'm' or sex == 'male':
        return '男'
    if sex == 'f' or sex == 'female':
        return '女'

def to_age(age: Optional[str]):
    if not age:
        return None
    if age[0] != '0':
        num = age[0:3]
    elif age[1] != '0':
        num = age[1:3]
    elif age[2] != '0':
        num = age[2]
    else:
        return None
    if age[3] == 'Y':
        return num + '岁'
    elif age[3] == 'M':
        return num + '月'
    elif age[3] == 'W':
        return num + '周'
    elif age[3] == 'D':
        return num + '天'

def get_dcm_img_with_info(path: str):
    dcm = dcmread(path)
    low = numpy.min(dcm.pixel_array)
    upp = numpy.max(dcm.pixel_array)
    # 16 bit -> 8 bit
    mat = numpy.floor_divide(dcm.pixel_array, (upp - low + 1) / 256)
    img = Image.fromarray(mat.astype(numpy.uint8)).toqpixmap()
    info = dict(
        患者ID=get_attr(dcm, 'PatientID'), 姓名=get_attr(dcm, 'PatientName'),
        出生日期=to_date(get_attr(dcm, 'PatientBirthDate')), 性别=to_sex(get_attr(dcm, 'PatientSex')),
        体重=get_attr(dcm, 'PatientWeigh'), 检查开始日期=to_date(get_attr(dcm, 'StudyDate')),
        检查日期=to_date(get_attr(dcm, 'SeriesDate')), 检查时患者年龄=to_age(get_attr(dcm, 'PatientAge')),
        检查部位=get_attr(dcm, 'BodyPartExamined')
    )
    for attr in info.keys():
        if not info[attr]:
            info[attr] = '（不详）'
    pixel_spacing = (dcm.PixelSpacing[0], dcm.PixelSpacing[1]) if hasattr(dcm, 'PixelSpacing') else None
    return img, '---\n\n'.join([f'{key}: {val}\n\n' for key, val in info.items()]), pixel_spacing

def rename_path_ext(path: str, ext: str):
    return os.path.splitext(path)[0] + ext

# windows 10
# sys_drive:\home_path\Pictures\
def get_home_img_dir():
    home_img_dir = os.getcwd()
    if sys_driver := os.getenv('SystemDrive'):
        home_img_dir = sys_driver
        if home_path := os.getenv('HomePath'):
            home_img_dir = os.path.join(home_img_dir, home_path, 'Pictures')
    return home_img_dir

def get_parent_dir(path: str):
    return os.path.dirname(os.path.abspath(path))

def load_from_json(path):
    with open(path, 'r') as file:
        return json.load(file)

def save_json_file(data: dict, path: str):
    with open(path, 'w') as file:
        json.dump(data, file, indent=config.indent)

def get_index_shift(a: QPointF):
    return QPointF(a.x() + config.index_shifting, a.y() - config.index_shifting)

def get_midpoint(a: QPointF, b: QPointF):
    return QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)

def get_distance(a: QPointF, b: QPointF):
    dis = ((a.x() - b.x()) * (a.x() - b.x()) + (a.y() - b.y()) * (a.y() - b.y())) ** 0.5
    return dis if dis > config.eps else config.eps

def get_distance_shift(a: QPointF, b: QPointF, c: QPointF):
    if math.fabs(a.x() - b.x()) < config.eps:
        return QPointF(c.x() + config.distance_shifting, c.y())
    if math.fabs(a.y() - b.y()) < config.eps:
        return QPointF(c.x(), c.y() - config.distance_shifting)
    if (a.x() - b.x()) * (a.y() - b.y()) < 0:
        return QPointF(c.x() + config.distance_shifting, c.y() + config.distance_shifting)
    return QPointF(c.x() + config.distance_shifting, c.y() - config.distance_shifting)

def get_radius(a: QPointF, b: QPointF, c: QPointF):
    return min(get_distance(b, a), get_distance(b, c)) * config.ratio_to_radius

def get_diag_points(a: QPointF, b: QPointF, c: QPointF):
    r = get_radius(a, b, c)
    return QPointF(b.x() - r, b.y() - r), QPointF(b.x() + r, b.y() + r)

def get_dis_point(a: QPointF, b: QPointF, dis: float):
    ratio = dis / get_distance(a, b)
    return QPointF(a.x() + (b.x() - a.x()) * ratio, a.y() + (b.y() - a.y()) * ratio)

def get_arc_midpoint(a: QPointF, b: QPointF, c: QPointF):
    return get_dis_point(
        b, get_midpoint(get_dis_point(b, a, config.base), get_dis_point(b, c, config.base)), get_radius(a, b, c)
    )

# ba · bc
def get_dot(a: QPointF, b: QPointF, c: QPointF):
    ba = (a.x() - b.x(), a.y() - b.y())
    bc = (c.x() - b.x(), c.y() - b.y())
    return ba[0] * bc[0] + ba[1] * bc[1]

# ba × bc
def get_cross(a: QPointF, b: QPointF, c: QPointF):
    ba = (a.x() - b.x(), a.y() - b.y())
    bc = (c.x() - b.x(), c.y() - b.y())
    return ba[0] * bc[1] - bc[0] * ba[1]

def get_degree(a: QPointF, b: QPointF, c: QPointF):
    return math.degrees(math.acos(min(1, max(-1, get_dot(a, b, c) / get_distance(b, a) / get_distance(b, c)))))

def get_begin_degree(a: QPointF, b: QPointF, c: QPointF):
    d = c if get_cross(a, b, c) > 0 else a
    deg = get_degree(d, b, QPointF(b.x() + config.base, b.y()))
    return 360 - deg if d.y() > b.y() else deg

def get_degree_shift(a: QPointF, b: QPointF):
    # up
    if a.y() > b.y() + config.eps and math.fabs(a.x() - b.x()) < config.eps:
        return QPointF(b.x(), b.y() - config.degree_shifting_base)
    # down
    if a.y() + config.eps < b.y() and math.fabs(a.x() - b.x()) < config.eps:
        return QPointF(b.x(), b.y() + config.degree_shifting_base)
    # left
    if a.x() > b.x() + config.eps and math.fabs(a.y() - b.y()) < config.eps:
        return QPointF(b.x() - config.degree_shifting_more, b.y())
    # right
    if a.x() + config.eps < b.x() and math.fabs(a.y() - b.y()) < config.eps:
        return QPointF(b.x() + config.degree_shifting_base, b.y())
    # top right
    if a.x() + config.eps < b.x() and a.y() > b.y() + config.eps:
        return QPointF(b.x() + config.degree_shifting_base, b.y() - config.degree_shifting_base)
    # top left
    if a.x() > b.x() + config.eps and a.y() > b.y() + config.eps:
        return QPointF(b.x() - config.degree_shifting_more, b.y() - config.degree_shifting_base)
    # bottom left
    if a.x() > b.x() + config.eps and a.y() + config.eps < b.y():
        return QPointF(b.x() - config.degree_shifting_more, b.y() + config.degree_shifting_base)
    # bottom right
    return QPointF(b.x() + config.degree_shifting_base, b.y() + config.degree_shifting_base)

def get_min_bounding_rect(a: QPointF, b: QPointF):
    r = get_distance(a, b)
    return QRectF(QPointF(a.x() - r, a.y() - r), QPointF(a.x() + r, a.y() + r))

def get_line_key(index_a: int, index_b: int):
    return (index_a, index_b) if index_a < index_b else (index_b, index_a)

def get_angle_key(index_a: int, index_b: int, index_c: int):
    return (index_a, index_b, index_c) if index_a < index_c else (index_c, index_b, index_a)

def is_on_a_line(a: QPointF, b: QPointF, c: QPointF):
    return math.fabs((a.x() - c.x()) * (a.y() - b.y()) - (a.x() - b.x()) * (a.y() - c.y())) < config.eps

# ab: da · x + db · y + dc = 0
def get_foot_point(a: QPointF, b: QPointF, c: QPointF):
    da = a.y() - b.y()
    db = b.x() - a.x()
    dc = -da * a.x() - db * a.y()
    return QPointF(
        (db * db * c.x() - da * db * c.y() - da * dc) / (da * da + db * db),
        (da * da * c.y() - da * db * c.x() - db * dc) / (da * da + db * db)
    )

def is_on_segment(a: QPointF, b: QPointF, c: QPointF):
    return min(a.x(), b.x()) < c.x() + config.eps and c.x() < max(a.x(), b.x()) + config.eps
