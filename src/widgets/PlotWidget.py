from PyQt6.QtWidgets import (
    QMenu, QVBoxLayout, QHBoxLayout, QDialog, QPushButton, QComboBox, QLabel
)
from PyQt6.QtCore import Qt, QSize

from widgets.DataWidget import DataWidget
from pyqtgraph import PlotWidget as QPlotter

from dataclasses import dataclass, asdict

from tools.Icons import createIcon
from datastreams.DataVariable import DataVariableSelector

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
        changeSignalsAction = menu.addAction("&Data sources")
        changeSignalsAction.triggered.connect(lambda: PlotWidgetDataSources(self).exec())

        plotSettAction = menu.addAction("&Plot settings")
        plotSettAction.triggered.connect(lambda: print("TODO!"))

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

class PlotWidgetDataSources(QDialog):
    def __init__(self, parent: PlotWidget = None):
        super().__init__(parent)
        self.parent = parent

        self.setWindowTitle(f'Data sources for {self.parent.parentWindowName}')

        parentGeo = self.parent.geometry()
        self.move(
            parentGeo.center().x() + parentGeo.width(),
            parentGeo.center().y() + parentGeo.height()
        )

        # Main layout.
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Top bar selection of the data source.
        sourceComboLabel = QLabel("Data source:")
        sourceComboLabel.setContentsMargins(0,0,10,0)

        self.sourceCombo = QComboBox()
        self.sourceCombo.setStatusTip("Select the source to modify its properties.")
        self.sourceCombo.setPlaceholderText("Add a new source first...")
        self.sourceCombo.setFixedHeight(30)
        self.sourceCombo.setMinimumContentsLength(50)
        self.sourceCombo.setEnabled(False)
        self.sourceCombo.currentTextChanged.connect(
            lambda: self.runAction('datasource-change', 'undo', 
                    (self.sourceCombo.currentText()))
        )

        self.addButton = QPushButton(createIcon(':datasource-add', "green"), "Add new source")
        self.addButton.setStatusTip('Add a new data source to the widget.')
        self.addButton.clicked.connect(lambda: self.runAction('datasource-new', 'undo'))
        self.addButton.setFixedWidth(150)
        self.addButton.setFixedHeight(30)
        self.addButton.setIconSize(QSize(20,20))

        self.removeButton = QPushButton(createIcon(':datasource-remove', "red"), "Remove source")
        self.removeButton.setStatusTip('Remove the selected data source from the widget.')
        self.removeButton.clicked.connect(lambda: self.runAction('datasource-remove', 'undo'))
        self.removeButton.setFixedWidth(150)
        self.removeButton.setFixedHeight(30)
        self.removeButton.setIconSize(QSize(20,20))

        dataSourceLayout = QHBoxLayout()
        dataSourceLayout.addWidget(sourceComboLabel)
        dataSourceLayout.addWidget(self.sourceCombo)
        dataSourceLayout.addStretch()
        dataSourceLayout.addWidget(self.addButton)
        dataSourceLayout.addWidget(self.removeButton)
        dataSourceLayout.addStretch()
        layout.addLayout(dataSourceLayout)

        # Add Apply and Cancel buttons.
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

    def runAction(self, action: str, actionStack: str | None, *args):
        if action == "datasource-new":
            DataVariableSelector(self).exec()
        elif action == "datasource-remove":
            pass
        elif action == "datasource-change":
            pass
        else:
            print(f'Action {action} is not defined on PlotWidgetDataSources')

    def applyChanges(self):
        self.accept()

    def discardChanges(self):
        self.close()
