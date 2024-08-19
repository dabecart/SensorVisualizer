from PyQt6.QtWidgets import QMdiArea, QRubberBand
from PyQt6.QtCore import QLine

from widgets.LineRubberBand import LineRubberBand

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