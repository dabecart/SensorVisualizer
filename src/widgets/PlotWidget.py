from PyQt6.QtWidgets import QMenu, QVBoxLayout, QHBoxLayout, QFormLayout, QDialog, QPushButton
from PyQt6.QtCore import Qt

from widgets.DataWidget import DataWidget
from pyqtgraph import PlotWidget as QPlotter

from dataclasses import dataclass, asdict

class PlotWidget(DataWidget):
    def __init__(self, parent=None, startArgs:dict[str, any] | None = None):
        self.plotter = Plotter(parent)
        super().__init__(parent, startArgs)

    @property
    def parentWindowName(self) -> str:
        return "Plot widget"

    def setContent(self, layout) -> None:
        layout.addWidget(self.plotter)

    # Convert all fields necessary for this window to a dictionary. This is used to create the 
    # save file. In this case, the geometry and the values of the inner widget.
    def toDict(self) -> dict[str, any]:
        return asdict(self.plotter)

    # Use the given startArgs to initiate the widget.
    def fromDict(self, startArgs: dict[str, any]):
        self.plotter.fromDict(startArgs)

    # Add the necessary items to the context menu.
    def addConfigToContextMenu(self, menu: QMenu):
        plotSettAction = menu.addAction("Plot settings")
        plotSettAction.triggered.connect(lambda: PlotWidgetConfigDialog(self).exec())

@dataclass
class Plotter(QPlotter):
    _plotTitle:  str     = ""
    _xLabel:     str     = ""
    _yLabel:     str     = ""
    _gridX:      bool    = False
    _gridY:      bool    = False
    _gridAlpha:  float   = 1.0
    _logModeX:   bool    = False
    _logModeY:   bool    = False

    @property
    def plotTitle(self):
        return self._plotTitle
    @plotTitle.setter
    def plotTitle(self, title: str):
        self.plotItem.setTitle(title)
        self._plotTitle = title

    @property
    def xLabel(self):
        return self._xLabel
    @xLabel.setter
    def xLabel(self, label: str):
        self.plotItem.setLabel('bottom', label)
        self._xLabel = label

    @property
    def yLabel(self):
        return self._yLabel
    @yLabel.setter
    def yLabel(self, label: str):
        self.plotItem.setLabel('left', label)
        self._yLabel = label

    def __init__(self, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent, background, plotItem, **kargs)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.plotItem.setMenuEnabled(False)
        self.plotItem.setContentsMargins(5,5,5,5)

    def showGrid(self, x: bool, y: bool, alpha: float = 1.0):
        self._gridX = x
        self._gridY = y
        self._gridAlpha = alpha
        self.plotItem.showGrid(x, y, alpha)

    def setLogMode(self, x: bool, y: bool):
        self._logModeX = x
        self._logModeY = y
        self.plotItem.setLogMode(x, y)
    
    def fromDict(self, startArgs: dict[str, any]):
        if startArgs is None:
            return

        self.plotTitle = startArgs.get("_plotTitle", "")
        self.xLabel = startArgs.get("_xLabel", "")
        self.yLabel = startArgs.get("_yLabel", "")
        self.showGrid(
            x = startArgs.get("_gridX", False),
            y = startArgs.get("_gridY", False),
            alpha = startArgs.get("_gridAlpha", 1.0)
        )
        self.setLogMode(
            x = startArgs.get("_logModeX", False),
            y = startArgs.get("_logModeY", False)
        )

class PlotWidgetConfigDialog(QDialog):
    def __init__(self, parent: PlotWidget = None):
        super().__init__(parent)
        self.parent = parent

        self.setWindowTitle(f'Settings for {self.parent.parentWindowName}')
        self.resize(300, 200)

        parentGeo = self.parent.geometry()
        self.move(
            parentGeo.center().x() + parentGeo.width(),
            parentGeo.center().y() + parentGeo.height()
        )

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add Apply and Cancel buttons
        buttonsLayout = QHBoxLayout()
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.discardChanges)
        self.applyButton = QPushButton('Apply')
        self.applyButton.clicked.connect(self.applyChanges)

        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.cancelButton)
        buttonsLayout.addWidget(self.applyButton)

        layout.addStretch()
        layout.addLayout(buttonsLayout)

    def applyChanges(self):
        pass

    def discardChanges(self):
        pass
