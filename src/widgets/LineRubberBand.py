from PyQt6.QtWidgets import QRubberBand
from PyQt6.QtCore import Qt, QRect, QLine, QPoint
from PyQt6.QtGui import  QPainter, QPen, QPaintEvent

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