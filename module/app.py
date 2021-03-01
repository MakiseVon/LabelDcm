from module import static
from module.config import config
from module.mode import LabelMode
from ui.form import Ui_Form
from PyQt5.QtCore import pyqtBoundSignal, QCoreApplication, QEvent, QObject, QPointF, QRectF, QSize, Qt
from PyQt5.QtGui import QColor, QCursor, QFont, QIcon, QMouseEvent, QPainter, QPen, QPixmap, QResizeEvent
from PyQt5.QtWidgets import QAction, QFileDialog, QGraphicsScene, QInputDialog, QMainWindow, QMenu, QMessageBox, \
                            QStatusBar
from typing import Dict, List, Optional, Set, Tuple

class LabelApp(QMainWindow, Ui_Form):
    def __init__(self):
        super(LabelApp, self).__init__()
        # Init UI
        self.setupUi(self)
        self.retranslateUi(self)
        with open('source/style.qss', 'r', encoding='utf-8') as file:
            self.setStyleSheet(file.read())
        self.init_color_box()
        self.color = QColor(config.defaultColor)
        self.init_action_box()
        self.mode = LabelMode.defaultMode
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        # Init Image Size
        self.imgSize = 1
        # Init Image
        self.src: Optional[QPixmap] = None
        self.img: Optional[QPixmap] = None
        self.path: Optional[str] = None
        self.ratioFromOld = 1
        self.ratioToSrc = 1
        # Init Events
        self.targetEventType = [QMouseEvent.MouseButtonPress, QMouseEvent.MouseMove, QMouseEvent.MouseButtonRelease]
        self.init_event_connections()
        # Init Indexs
        self.indexA = -1
        self.indexB = -1
        self.indexC = -1
        # A: IndexA - A, Color
        self.points: Dict[int, Tuple[QPointF, QColor]] = {}
        # AB: IndexA, IndexB - Color
        self.lines: Dict[Tuple[int, int], QColor] = {}
        # ∠ABC: IndexA, IndexB, IndexC - Color
        self.angles: Dict[Tuple[int, int, int], QColor] = {}
        # ⊙A, r = AB: IndexA, IndexB - Color
        self.circles: Dict[Tuple[int, int], QColor] = {}
        # Init Pivots
        self.pivots: Set[int] = set()
        # Init Highlight
        self.highlightMoveIndex = -1
        self.highlightPoints: Set[int] = set()
        # Init Right Button Menu
        self.rightBtnMenu = QMenu(self)

    def init_color_box(self):
        size = self.colorBox.iconSize()
        index = 0
        defaultIndex = -1
        for color in config.colorList:
            if color == config.defaultColor:
                defaultIndex = index
            colorIcon = QPixmap(size)
            colorIcon.fill(QColor(color))
            self.colorBox.addItem(QIcon(colorIcon), f'  {color.capitalize()}')
            index += 1
        self.colorBox.setCurrentIndex(defaultIndex)

    def init_action_box(self):
        index = 0
        defaultIndex = -1
        for action in config.actionList:
            if action == config.defaultAction:
                defaultIndex = index
            self.actionBox.addItem(f'    {action}')
            index += 1
        self.actionBox.setCurrentIndex(defaultIndex)

    def init_event_connections(self):
        self.imgView.viewport().installEventFilter(self)
        self.loadImgBtn.triggered.connect(self.upload_img)
        self.deleteImgBtn.triggered.connect(self.delete_img)
        self.saveImgBtn.triggered.connect(self.save_img)
        self.importBtn.triggered.connect(self.import_labels)
        self.exportAllBtn.triggered.connect(self.export_all)
        self.exportPivotsBtn.triggered.connect(self.export_pivots)
        self.quitAppBtn.triggered.connect(QCoreApplication.instance().quit)
        self.incSizeBtn.triggered.connect(self.inc_img_size)
        self.decSizeBtn.triggered.connect(self.dec_img_size)
        self.resetSizeBtn.triggered.connect(self.reset_img_size)
        self.clearAllBtn.triggered.connect(self.clear_labels)
        self.colorBox.currentIndexChanged.connect(self.change_color)
        self.actionBox.currentIndexChanged.connect(self.switch_mode)
        self.imgSizeSlider.valueChanged.connect(self.set_img_size_slider)
        self.autoAddPtsBtn.triggered.connect(self.auto_add_points)

    def reset_img(self):
        self.src = None
        self.img = None
        self.path = None
        self.ratioFromOld = 1
        self.ratioToSrc = 1
        self.patientInfo.setMarkdown('')

    def reset_index(self):
        self.indexA = -1
        self.indexB = -1
        self.indexC = -1

    def reset_highlight(self):
        self.highlightMoveIndex = -1
        self.highlightPoints.clear()

    def reset_except_img(self):
        self.reset_index()
        self.points.clear()
        self.lines.clear()
        self.angles.clear()
        self.circles.clear()
        self.pivots.clear()
        self.reset_highlight()

    def reset_all(self):
        self.reset_img()
        self.reset_except_img()

    def update_img(self):
        if not self.src:
            self.reset_img()
            return None
        old = self.img if self.img else self.src
        size = QSize(
            (self.imgView.width() - 2 * self.imgView.lineWidth()) * self.imgSize,
            (self.imgView.height() - 2 * self.imgView.lineWidth()) * self.imgSize
        )
        self.img = self.src.scaled(size, Qt.KeepAspectRatio)
        self.ratioFromOld = self.img.width() / old.width()
        self.ratioToSrc = self.src.width() / self.img.width()

    def update_points(self):
        if not self.img or not self.points or self.ratioFromOld == 1:
            return None
        for point, _ in self.points.values():
            point.setX(point.x() * self.ratioFromOld)
            point.setY(point.y() * self.ratioFromOld)
        self.ratioFromOld = 1

    def get_src_point(self, point: QPointF):
        return QPointF(point.x() * self.ratioToSrc, point.y() * self.ratioToSrc)

    def get_img_point(self, point: QPointF):
        return QPointF(point.x() / self.ratioToSrc, point.y() / self.ratioToSrc)

    def label_points(self, img: Optional[QPixmap], toSrc: bool):
        if not img or not self.points:
            return None
        painter = QPainter()
        painter.begin(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen()
        pen.setCapStyle(Qt.RoundCap)
        font = QFont('Consolas')
        if toSrc:
            pen.setWidthF(config.pointWidth * self.ratioToSrc)
            font.setPointSizeF(config.fontSize * self.ratioToSrc)
        else:
            pen.setWidthF(config.pointWidth)
            font.setPointSizeF(config.fontSize)
        painter.setFont(font)
        for index, (point, color) in self.points.items():
            labelPoint: QPointF
            if toSrc:
                pen.setColor(color)
                labelPoint = self.get_src_point(point)
            else:
                pen.setColor(
                    color if index != self.highlightMoveIndex and index not in self.highlightPoints
                    else QColor.lighter(color)
                )
                labelPoint = point
            painter.setPen(pen)
            painter.drawPoint(labelPoint)
            painter.drawText(static.get_index_shift(labelPoint), str(index))
        painter.end()

    def label_lines(self, img: Optional[QPixmap], toSrc: bool):
        if not img or not self.lines:
            return None
        painter = QPainter()
        painter.begin(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen()
        pen.setCapStyle(Qt.RoundCap)
        font = QFont('Consolas')
        if toSrc:
            pen.setWidthF(config.lineWidth * self.ratioToSrc)
            font.setPointSizeF(config.fontSize * self.ratioToSrc)
        else:
            pen.setWidthF(config.lineWidth)
            font.setPointSizeF(config.fontSize)
        painter.setFont(font)
        for (indexA, indexB), color in self.lines.items():
            isHighlight = indexA in self.highlightPoints and indexB in self.highlightPoints \
                          and (self.mode == LabelMode.angleMode or self.mode == LabelMode.verticalMode)
            pen.setColor(QColor.lighter(color) if isHighlight else color)
            painter.setPen(pen)
            A = self.points[indexA][0]
            B = self.points[indexB][0]
            srcA = self.get_src_point(A)
            srcB = self.get_src_point(B)
            labelPoint: QPointF
            if toSrc:
                painter.drawLine(srcA, srcB)
                labelPoint = static.get_midpoint(srcA, srcB)
            else:
                painter.drawLine(A, B)
                labelPoint = static.get_midpoint(A, B)
            painter.drawText(
                static.get_distance_shift(A, B, labelPoint), str(round(static.get_distance(srcA, srcB), 2))
            )
        painter.end()

    def label_angles(self, img: Optional[QPixmap], toSrc: bool):
        if not img or not self.angles:
            return None
        painter = QPainter()
        painter.begin(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen()
        pen.setCapStyle(Qt.RoundCap)
        font = QFont('Consolas')
        if toSrc:
            pen.setWidthF(config.angleWidth * self.ratioToSrc)
            font.setPointSizeF(config.fontSize * self.ratioToSrc)
        else:
            pen.setWidthF(config.angleWidth)
            font.setPointSizeF(config.fontSize)
        painter.setFont(font)
        for (indexA, indexB, indexC), color in self.angles.items():
            pen.setColor(color)
            painter.setPen(pen)
            A = self.points[indexA][0]
            B = self.points[indexB][0]
            C = self.points[indexC][0]
            D, E = static.get_diag_points(self.points[indexA][0], B, C)
            F = static.get_arc_midpoint(A, B, C)
            labelRect: QRectF
            labelPointA: QPointF
            labelPointB: QPointF
            if toSrc:
                labelRect = QRectF(self.get_src_point(D), self.get_src_point(E))
                labelPointA = self.get_src_point(B)
                labelPointB = self.get_src_point(F)
            else:
                labelRect = QRectF(D, E)
                labelPointA = B
                labelPointB = F
            deg = static.get_degree(A, B, C)
            painter.drawArc(labelRect, int(static.get_begin_degree(A, B, C) * 16), int(deg * 16))
            painter.drawText(static.get_degree_shift(labelPointA, labelPointB), str(round(deg, 2)) + '°')
        painter.end()

    def label_circles(self, img: Optional[QPixmap], toSrc: bool):
        if not img or not self.circles:
            return None
        painter = QPainter()
        painter.begin(img)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen()
        pen.setCapStyle(Qt.RoundCap)
        pen.setWidthF(config.lineWidth if not toSrc else config.lineWidth * self.ratioToSrc)
        for (indexA, indexB), color in self.circles.items():
            isHighlight = indexA in self.highlightPoints and indexB in self.highlightPoints \
                          and self.mode == LabelMode.circleMode
            pen.setColor(QColor.lighter(color) if isHighlight else color)
            painter.setPen(pen)
            A = self.points[indexA][0]
            B = self.points[indexB][0]
            painter.drawEllipse(
                static.get_min_bounding_rect(A, B) if not toSrc
                else static.get_min_bounding_rect(self.get_src_point(A), self.get_src_point(B))
            )
        painter.end()

    def update_labels(self, img: Optional[QPixmap], toSrc: bool):
        self.label_points(img, toSrc)
        self.label_lines(img, toSrc)
        self.label_angles(img, toSrc)
        self.label_circles(img, toSrc)

    def update_img_view(self):
        scene = QGraphicsScene()
        if self.img:
            scene.addPixmap(self.img)
        self.imgView.setScene(scene)

    def update_pivots_info(self):
        if not self.img or not self.points or not self.pivots:
            self.pivotsInfo.setMarkdown('')
            return None
        pivots = list(self.pivots)
        pivots.sort()
        mdInfo = ''
        for index in pivots:
            point = self.get_src_point(self.points[index][0])
            mdInfo += f'{index}: ({round(point.x(), 2)}, {round(point.y(), 2)})\n\n'
        self.pivotsInfo.setMarkdown(mdInfo)

    def update_all(self):
        self.update_img()
        self.update_points()
        self.update_labels(self.img, False)
        self.update_img_view()
        self.update_pivots_info()

    def resizeEvent(self, _: QResizeEvent):
        self.update_all()

    def get_point_index(self, point: QPointF):
        if not self.img or not self.points:
            return -1
        distance = config.pointWidth - config.eps
        # Index -1 means the point does not exist
        index = -1
        for idx, (pt, _) in self.points.items():
            dis = static.get_distance(point, pt)
            if dis < distance:
                distance = dis
                index = idx
        return index

    def is_point_out_of_bound(self, point: QPointF):
        return point.x() < config.pointWidth / 2 or point.x() > self.img.width() - config.pointWidth / 2 \
               or point.y() < config.pointWidth / 2 or point.y() > self.img.height() - config.pointWidth / 2

    def get_index_cnt(self):
        return len([i for i in [self.indexA, self.indexB, self.indexC] if i != -1])

    def trigger_index(self, index: int):
        if not self.img or not self.points or index == -1:
            return None
        if index in [self.indexA, self.indexB, self.indexC]:
            indexs = [i for i in [self.indexA, self.indexB, self.indexC] if i != index]
            self.indexA = indexs[0]
            self.indexB = indexs[1]
            self.indexC = -1
            self.highlightPoints.remove(index)
        else:
            indexs = [i for i in [self.indexA, self.indexB, self.indexC] if i != -1]
            indexs.append(index)
            while len(indexs) < 3:
                indexs.append(-1)
            self.indexA = indexs[0]
            self.indexB = indexs[1]
            self.indexC = indexs[2]
            self.highlightPoints.add(index)

    def end_trigger(self):
        self.reset_index()
        self.reset_highlight()

    def end_trigger_with(self, index: int):
        self.end_trigger()
        self.highlightMoveIndex = index

    def get_new_index(self):
        return max(self.points.keys() if self.points else [0]) + 1

    def add_new_point(self, point: QPointF):
        if self.img:
            index = self.get_new_index()
            self.points[index] = point, self.color
            return index

    def add_line(self, indexA: int, indexB: int):
        if self.img and indexA in self.points and indexB in self.points:
            self.lines[static.get_line_key(indexA, indexB)] = self.color

    def add_angle(self, indexA: int, indexB: int, indexC: int):
        if self.img and static.get_line_key(indexA, indexB) in self.lines \
                and static.get_line_key(indexB, indexC) in self.lines:
            self.angles[static.get_angle_key(indexA, indexB, indexC)] = self.color

    def add_circle(self, indexA: int, indexB: int):
        if self.img and indexA in self.points and indexB in self.points:
            self.circles[(indexA, indexB)] = self.color

    def erase_point(self, index):
        if index not in self.points:
            return None
        del self.points[index]
        for line in list(self.lines.keys()):
            if index in line:
                del self.lines[line]
        for angle in list(self.angles.keys()):
            if index in angle:
                del self.angles[angle]
        for circle in list(self.circles.keys()):
            if index in circle:
                del self.circles[circle]
        self.pivots.discard(index)

    def erase_highlight(self):
        if self.mode == LabelMode.circleMode:
            self.erase_point(self.indexB)
        self.reset_index()
        self.reset_highlight()
        self.update_all()

    def handle_point_mode(self, evt: QMouseEvent):
        if evt.type() != QMouseEvent.MouseButtonPress or evt.button() != Qt.LeftButton:
            return None
        point = self.imgView.mapToScene(evt.pos())
        index = self.get_point_index(point)
        if index == -1:
            self.add_new_point(point)
        else:
            self.points[index] = self.points[index][0], self.color
        self.update_all()

    def handle_line_mode(self, evt: QMouseEvent):
        if evt.type() != QMouseEvent.MouseButtonPress or evt.button() != Qt.LeftButton:
            return None
        point = self.imgView.mapToScene(evt.pos())
        index = self.get_point_index(point)
        self.trigger_index(self.add_new_point(point) if index == -1 else index)
        if self.get_index_cnt() == 2:
            self.add_line(self.indexA, self.indexB)
            self.end_trigger_with(self.indexB)
        self.update_all()

    def handle_angle_mode(self, evt: QMouseEvent):
        if evt.type() != QMouseEvent.MouseButtonPress or evt.button() != Qt.LeftButton:
            return None
        self.trigger_index(self.get_point_index(self.imgView.mapToScene(evt.pos())))
        if self.get_index_cnt() == 2 and static.get_line_key(self.indexA, self.indexB) not in self.lines:
            self.trigger_index(self.indexA)
        elif self.get_index_cnt() == 3:
            if static.get_line_key(self.indexB, self.indexC) in self.lines:
                self.add_angle(self.indexA, self.indexB, self.indexC)
                self.end_trigger_with(self.indexC)
            else:
                indexC = self.indexC
                self.end_trigger()
                self.trigger_index(indexC)
        self.update_all()

    def handle_circle_mode(self, evt: QMouseEvent):
        point = self.imgView.mapToScene(evt.pos())
        if evt.type() == QMouseEvent.MouseButtonPress and evt.button() == Qt.LeftButton:
            if self.get_index_cnt() == 0:
                index = self.get_point_index(point)
                self.trigger_index(self.add_new_point(point) if index == -1 else index)
                self.trigger_index(
                    self.add_new_point(QPointF(point.x() + 2 * config.eps, point.y() + 2 * config.eps))
                )
                self.add_circle(self.indexA, self.indexB)
            elif self.get_index_cnt() == 2:
                self.end_trigger_with(self.indexB)
        elif evt.type() == QMouseEvent.MouseMove and self.get_index_cnt() == 2 \
                and not self.is_point_out_of_bound(point):
            self.points[self.indexB][0].setX(point.x())
            self.points[self.indexB][0].setY(point.y())
        self.update_all()

    def handle_midpoint_mode(self, evt: QMouseEvent):
        if evt.type() != QMouseEvent.MouseButtonPress or evt.button() != Qt.LeftButton:
            return None
        self.trigger_index(self.get_point_index(self.imgView.mapToScene(evt.pos())))
        if self.get_index_cnt() == 2:
            if static.get_line_key(self.indexA, self.indexB) in self.lines:
                A = self.points[self.indexA][0]
                B = self.points[self.indexB][0]
                indexC = self.add_new_point(static.get_midpoint(A, B))
                self.add_line(self.indexA, indexC)
                self.add_line(self.indexB, indexC)
                self.end_trigger_with(self.indexB)
            else:
                self.trigger_index(self.indexA)
        self.update_all()

    def handle_vertical_mode(self, evt: QMouseEvent):
        if evt.type() != QMouseEvent.MouseButtonPress or evt.button() != Qt.LeftButton:
            return None
        self.trigger_index(self.get_point_index(self.imgView.mapToScene(evt.pos())))
        if self.get_index_cnt() == 2:
            if static.get_line_key(self.indexA, self.indexB) not in self.lines:
                self.trigger_index(self.indexA)
        elif self.get_index_cnt() == 3:
            A = self.points[self.indexA][0]
            B = self.points[self.indexB][0]
            C = self.points[self.indexC][0]
            if static.is_on_a_line(A, B, C):
                if static.get_line_key(self.indexB, self.indexC) in self.lines:
                    self.trigger_index(self.indexA)
                else:
                    indexC = self.indexC
                    self.end_trigger()
                    self.trigger_index(indexC)
            else:
                D = static.get_foot_point(A, B, C)
                indexD = self.add_new_point(D)
                if not static.is_on_segment(A, B, D):
                    self.add_line(
                        (self.indexA if static.get_distance(A, D) < static.get_distance(B, D) else self.indexB), indexD
                    )
                self.add_line(self.indexC, indexD)
                self.end_trigger_with(self.indexC)
            self.update_all()

    def handle_drag_mode(self, evt: QMouseEvent):
        point = self.imgView.mapToScene(evt.pos())
        if evt.type() == QMouseEvent.MouseButtonPress and evt.button() == Qt.LeftButton and self.get_index_cnt() == 0:
            self.trigger_index(self.get_point_index(point))
        elif evt.type() == QMouseEvent.MouseMove and self.get_index_cnt() == 1 \
                and not self.is_point_out_of_bound(point):
            self.points[self.indexA][0].setX(point.x())
            self.points[self.indexA][0].setY(point.y())
        elif evt.type() == QMouseEvent.MouseButtonRelease and self.get_index_cnt() == 1:
            self.trigger_index(self.indexA)
        self.update_all()

    def handle_erase_point_mode(self, evt: QMouseEvent):
        index = self.get_point_index(self.imgView.mapToScene(evt.pos()))
        if evt.type() == QMouseEvent.MouseButtonPress and evt.button() == Qt.LeftButton and index != -1:
            self.erase_point(index)
        self.update_all()

    def handle_highlight_move(self, evt: QMouseEvent):
        point = self.imgView.mapToScene(evt.pos())
        self.highlightMoveIndex = self.get_point_index(point)
        point = self.get_src_point(point)
        text = f'坐标：{round(point.x(), 2)}, {round(point.y(), 2)}'
        self.statusBar.showMessage(text, 1000)
        self.update_all()

    def modify_index(self, index: int):
        newIndex, modify = QInputDialog.getInt(self, '更改标号', '请输入一个新的标号', index, 0, step=1)
        if not modify or newIndex == index:
            return None
        if newIndex <= 0:
            self.warning('标号必须为正整数！')
            return None
        if newIndex in self.points:
            self.warning('此标号已存在！')
            return None
        self.points[newIndex] = self.points[index]
        del self.points[index]
        for line in list(self.lines.keys()):
            if index in line:
                fixedIndex = line[0] + line[1] - index
                self.lines[static.get_line_key(newIndex, fixedIndex)] = self.lines[line]
                del self.lines[line]
        for angle in list(self.angles.keys()):
            if index in angle:
                if index == angle[1]:
                    self.angles[angle[0], newIndex, angle[2]] = self.angles[angle]
                else:
                    fixedIndex = angle[0] + angle[2] - index
                    self.angles[static.get_angle_key(newIndex, angle[1], fixedIndex)] = self.angles[angle]
                del self.angles[angle]
        for circle in list(self.circles.keys()):
            if index in circle:
                if index == circle[0]:
                    self.circles[(newIndex, circle[1])] = self.circles[circle]
                else:
                    self.circles[(circle[0], newIndex)] = self.circles[circle]
                del self.circles[circle]
        if index in self.pivots:
            self.pivots.remove(index)
            self.pivots.add(newIndex)

    def add_pivots(self, index: int):
        if self.img and index in self.points:
            self.pivots.add(index)

    def remove_pivots(self, index: int):
        if self.img and self.pivots:
            self.pivots.discard(index)

    def switch_pivot_state(self, index: int):
        if index not in self.pivots:
            self.add_pivots(index)
        else:
            self.remove_pivots(index)

    def create_right_btn_menu(self, index: int, point: QPointF):
        self.rightBtnMenu = QMenu(self)
        modifyIndex = QAction('更改标号', self.rightBtnMenu)
        modifyIndexTriggered: pyqtBoundSignal = modifyIndex.triggered
        modifyIndexTriggered.connect(lambda: self.modify_index(index))
        switchPivotState = QAction('删除该点信息' if index in self.pivots else '查看该点信息', self.rightBtnMenu)
        switchPivotStateTriggered: pyqtBoundSignal = switchPivotState.triggered
        switchPivotStateTriggered.connect(lambda: self.switch_pivot_state(index))
        erasePoint = QAction('清除该点', self.rightBtnMenu)
        erasePointTriggered: pyqtBoundSignal = erasePoint.triggered
        erasePointTriggered.connect(lambda: self.erase_point(index))
        self.rightBtnMenu.addAction(modifyIndex)
        self.rightBtnMenu.addAction(switchPivotState)
        self.rightBtnMenu.addAction(erasePoint)
        self.rightBtnMenu.exec(point)

    def handle_right_btn_menu(self, evt: QMouseEvent):
        if (index := self.get_point_index(self.imgView.mapToScene(evt.pos()))) != -1:
            self.erase_highlight()
            self.highlightMoveIndex = index
            self.update_all()
            self.create_right_btn_menu(index, evt.globalPos())
            self.highlightMoveIndex = self.get_point_index(
                self.imgView.mapToScene(self.imgView.mapFromParent(self.mapFromParent(QCursor.pos())))
            )
            self.update_all()

    def eventFilter(self, obj: QObject, evt: QEvent):
        if not self.img or obj is not self.imgView.viewport() or evt.type() not in self.targetEventType:
            return super().eventFilter(obj, evt)
        if self.mode == LabelMode.pointMode:
            self.handle_point_mode(evt)
        elif self.mode == LabelMode.lineMode:
            self.handle_line_mode(evt)
        elif self.mode == LabelMode.angleMode:
            self.handle_angle_mode(evt)
        elif self.mode == LabelMode.circleMode:
            self.handle_circle_mode(evt)
        elif self.mode == LabelMode.midpointMode:
            self.handle_midpoint_mode(evt)
        elif self.mode == LabelMode.verticalMode:
            self.handle_vertical_mode(evt)
        elif self.mode == LabelMode.movePointMode:
            self.handle_drag_mode(evt)
        elif self.mode == LabelMode.erasePointMode:
            self.handle_erase_point_mode(evt)
        if evt.type() == QMouseEvent.MouseMove:
            self.handle_highlight_move(evt)
        elif evt.type() == QMouseEvent.MouseButtonPress and QMouseEvent(evt).button() == Qt.RightButton:
            self.handle_right_btn_menu(evt)
        return super().eventFilter(obj, evt)

    def warning(self, text: str):
        QMessageBox.warning(self, '警告', text)

    # DICOM (*.dcm)
    def load_dcm_img(self, imgPath: str):
        if static.is_file_readable(imgPath):
            self.src, mdInfo = static.get_dcm_img_and_md_info(imgPath)
            self.path = imgPath
            if path := imgPath.split('.'):
                if path[-1].lower() == 'dcm':
                    self.path = f'{imgPath[:-4]}.jpg'
            self.patientInfo.setMarkdown(mdInfo)
            self.update_all()
        else:
            self.warning('Dicom 文件不存在或不可读！')

    # JPEG (*.jpg;*.jpeg;*.jpe), PNG (*.png)
    def load_img(self, imgPath: str):
        if static.is_file_readable(imgPath):
            self.src = QPixmap()
            self.src.load(imgPath)
            self.path = imgPath
            self.update_all()
        else:
            self.warning('图片文件不存在或不可读！')

    def upload_img(self):
        caption = '新建'
        extFilter = 'DICOM (*.dcm);;JPEG (*.jpg;*.jpeg;*.jpe);;PNG (*.png)'
        dcmFilter = 'DICOM (*.dcm)'
        imgPath, imgExt = QFileDialog.getOpenFileName(self, caption, static.get_home_img_dir(), extFilter, dcmFilter)
        if not imgPath:
            return None
        self.reset_all()
        if imgExt == dcmFilter:
            self.load_dcm_img(imgPath)
        else:
            self.load_img(imgPath)

    def delete_img(self):
        if not self.src:
            self.warning('请先新建一个项目！')
            return None
        self.reset_all()
        self.update_all()

    def save_img(self):
        if not self.src:
            self.warning('请先新建一个项目！')
            return None
        img = self.src.copy()
        self.erase_highlight()
        self.update_labels(img, True)
        caption = '保存'
        extFilter = 'JPEG (*.jpg;*.jpeg;*.jpe);;PNG (*.png)'
        initFilter = 'JPEG (*.jpg;*.jpeg;*.jpe)'
        imgPath, _ = QFileDialog.getSaveFileName(self, caption, self.path, extFilter, initFilter)
        if imgPath:
            img.save(imgPath)

    def import_labels(self):
        if not self.img:
            self.warning('请先新建一个项目！')
            return None
        caption = '导入'
        initPath = static.get_home_img_dir()
        if path := self.path.split('.'):
            defaultPath = f'{self.path[:-(len(path[-1]) + 1)]}.json'
            if static.is_file_exists(defaultPath):
                initPath = defaultPath
        jsonFilter = 'JSON (*.json)'
        jsonPath, _ = QFileDialog.getOpenFileName(self, caption, initPath, jsonFilter)
        if not jsonPath:
            return None
        if not static.is_file_readable(jsonPath):
            self.warning('JSON 文件不存在或不可读！')
        if data := static.load_from_json(jsonPath):
            self.reset_except_img()
            if len(data) == 1:
                pivots: List[Tuple[int, float, float]] = data['pivots']
                for index, x, y in pivots:
                    self.points[index] = self.get_img_point(QPointF(x, y)), self.color
                    self.pivots.add(index)
            else:
                points: List[Tuple[int, float, float, str]] = data['points']
                for index, x, y, color in points:
                    self.points[index] = self.get_img_point(QPointF(x, y)), QColor(color)
                lines: List[Tuple[int, int, str]] = data['lines']
                for indexA, indexB, color in lines:
                    self.lines[static.get_line_key(indexA, indexB)] = QColor(color)
                angles: List[Tuple[int, int, int, str]] = data['angles']
                for indexA, indexB, indexC, color in angles:
                    self.angles[static.get_angle_key(indexA, indexB, indexC)] = QColor(color)
                circles: List[Tuple[int, int, str]] = data['circles']
                for indexA, indexB, color in circles:
                    self.circles[(indexA, indexB)] = QColor(color)
                self.pivots = set(data['pivots'])
            self.update_all()

    def export_all(self):
        if not self.img:
            self.warning('请先新建一个项目！')
            return None
        caption = '导出全部'
        initPath = static.get_home_img_dir()
        if path := self.path.split('.'):
            initPath = f'{self.path[:-(len(path[-1]) + 1)]}.json'
        jsonFilter = 'JSON (*.json)'
        jsonPath, _ = QFileDialog.getSaveFileName(self, caption, initPath, jsonFilter)
        if not jsonPath:
            return None
        if static.is_file_exists(jsonPath) and not static.is_file_writable(jsonPath):
            self.warning('JSON 文件不可读！')
            return None
        data = {'points': [], 'lines': [], 'angles': [], 'circles': [], 'pivots': []}
        points: List[Tuple[int, float, float, str]] = data['points']
        for index, point in self.points.items():
            srcPoint = self.get_src_point(point[0])
            points.append((index, srcPoint.x(), srcPoint.y(), point[1].name()))
        lines: List[Tuple[int, int, str]] = data['lines']
        for index, color in self.lines.items():
            lines.append((index[0], index[1], color.name()))
        angles: List[Tuple[int, int, int, str]] = data['angles']
        for index, color in self.angles.items():
            angles.append((index[0], index[1], index[2], color.name()))
        circles: List[Tuple[int, int, str]] = data['circles']
        for index, color in self.circles.items():
            circles.append((index[0], index[1], color.name()))
        data['pivots'] = list(self.pivots)
        static.save_json_file(data, jsonPath)

    def export_pivots(self):
        if not self.img:
            self.warning('请先新建一个项目！')
            return None
        caption = '导出关键点'
        initPath = static.get_home_img_dir()
        if path := self.path.split('.'):
            initPath = f'{self.path[:-(len(path[-1]) + 1)]}_pivots.json'
        jsonFilter = 'JSON (*.json)'
        jsonPath, _ = QFileDialog.getSaveFileName(self, caption, initPath, jsonFilter)
        if not jsonPath:
            return None
        if static.is_file_exists(jsonPath) and not static.is_file_writable(jsonPath):
            self.warning('JSON 文件不可读！')
            return None
        data = {'pivots': []}
        pivots: List[Tuple[int, float, float]] = data['pivots']
        for index in self.pivots:
            point = self.get_src_point(self.points[index][0])
            pivots.append((index, point.x(), point.y()))
        static.save_json_file(data, jsonPath)

    def inc_img_size(self):
        size = min(int(self.imgSize * 100 + 10), 200)
        self.imgSizeSlider.setValue(size)
        self.imgSize = size / 100
        self.imgSizeLabel.setText(f'大小：{size}%')
        self.update_all()

    def dec_img_size(self):
        size = max(int(self.imgSize * 100 - 10), 50)
        self.imgSizeSlider.setValue(size)
        self.imgSize = size / 100
        self.imgSizeLabel.setText(f'大小：{size}%')
        self.update_all()

    def reset_img_size(self):
        size = 100
        self.imgSizeSlider.setValue(size)
        self.imgSize = size / 100
        self.imgSizeLabel.setText(f'大小：{size}%')
        self.update_all()

    def clear_labels(self):
        if not self.img:
            return None
        self.reset_except_img()
        self.update_all()

    def change_color(self):
        self.color = QColor(config.colorList[self.colorBox.currentIndex()])

    def switch_mode(self):
        self.erase_highlight()
        text = config.actionList[self.actionBox.currentIndex()]
        mode: LabelMode
        if text == '点':
            mode = LabelMode.pointMode
        elif text == '线':
            mode = LabelMode.lineMode
        elif text == '角度':
            mode = LabelMode.angleMode
        elif text == '圆':
            mode = LabelMode.circleMode
        elif text == '中点':
            mode = LabelMode.midpointMode
        elif text == '直角':
            mode = LabelMode.verticalMode
        elif text == '移动点':
            mode = LabelMode.movePointMode
        elif text == '删除点':
            mode = LabelMode.erasePointMode
        else:
            mode = LabelMode.defaultMode
        self.mode = mode

    def set_img_size_slider(self):
        size = self.imgSizeSlider.value()
        self.imgSize = size / 100
        self.imgSizeLabel.setText(f'大小：{size}%')
        self.update_all()

    def add_real_point(self, index, x: float, y: float):
        if self.img:
            self.points[index] = self.get_img_point(QPointF(x, y)), self.color

    def add_new_real_point(self, x: float, y: float):
        self.add_real_point(self.get_new_index(), x, y)

    # TODO
    # add_real_point(index, x, y) or add_new_real_point(x, y)
    '''
    ----------> x
    |
    |
    |
    ↓
    y
    '''
    def auto_add_points(self):
        pass
