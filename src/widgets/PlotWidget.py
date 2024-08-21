from widgets.DataWidget import DataWidget
from pyqtgraph import PlotWidget as QPlotter

class PlotWidget(DataWidget):
    def __init__(self, parent=None, startArgs:dict[str, any] | None = None):
        self.plotter = QPlotter()

        super().__init__(parent, startArgs)

    @property
    def parentWindowName(self) -> str:
        return "Plot widget"

    def setContent(self, layout) -> None:
        layout.addWidget(self.plotter)

    # Convert all fields necessary for this window to a dictionary. This is used to create the 
    # save file. In this case, the geometry and the values of the inner widget.
    def toDict(self) -> dict[str, any]:
        pass

    # Use the given startArgs to initiate the widget.
    def fromDict(self, startArgs:dict[str, any]):
        pass
