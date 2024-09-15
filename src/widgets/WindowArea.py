# **************************************************************************************************
# @file WindowArea.py
# @brief Inherits from QMdiArea. The main container for widgets.Window objects.
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-09-15
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import QMdiArea, QRubberBand
from PyQt6.QtCore import QLine, Qt, QRect, QPoint
from PyQt6.QtGui import  QPainter, QPen, QPaintEvent

class WindowArea(QMdiArea):
    def __init__(self):
        super().__init__()
        self.bands: list[QRubberBand]       = []

    def setHintLines(self, listHintLines: list[QLine]):
        for band in self.bands:
            band.hide()
        self.bands.clear()

        for line in listHintLines:
            band = LineRubberBand(self)
            band.setLine(line)
            band.show()
            self.bands.append(band)

class LineRubberBand(QRubberBand):
    def __init__(self, parent=None):
        super(LineRubberBand, self).__init__(QRubberBand.Shape.Line, parent)
        self.line: QLine | None = None

    def paintEvent(self, event: QPaintEvent):
        if self.line is None:
            return
        
        pen = QPen(self.palette().highlight(), 2, cap=Qt.PenCapStyle.RoundCap)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)

        # This is calculated here because in the setLine method doesn't work...
        rect = self.rect()
        if self.line.dx() >= 0:
            if self.line.dy() >= 0:
                painter.drawLine(rect.topLeft(), rect.bottomRight())
            else:
                painter.drawLine(rect.bottomLeft(), rect.topRight())

        else:
            if self.line.dy() >= 0:
                painter.drawLine(rect.topRight(), rect.bottomLeft())
            else:
                painter.drawLine(rect.bottomRight(), rect.topLeft())

    def setLine(self, line: QLine):
        self.line = line
        minX = min(line.x1(), line.x2())
        maxX = max(line.x1(), line.x2())
        minY = min(line.y1(), line.y2())
        maxY = max(line.y1(), line.y2())

        rect = QRect(QPoint(minX, minY), QPoint(maxX, maxY))

        self.setGeometry(rect)