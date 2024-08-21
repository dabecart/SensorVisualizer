from dataclasses import dataclass
from abc import ABC, abstractmethod

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLayout

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from Window import Window

# Metaclass to be able to create DataWidget. This one will share both meta of QWidget and ABC. 
class QWidgetABCMeta(type(QWidget), type(ABC)):
    pass

class DataWidget(QWidget, ABC, metaclass=QWidgetABCMeta):

    @property
    @abstractmethod
    def parentWindowName(self) -> str:
        pass

    # Add the widget's content to the layout.
    @abstractmethod
    def setContent(self, layout: QLayout) -> None:
        pass

    # Convert all fields necessary for this widget to a dictionary. This is used to create the 
    # save file.
    @abstractmethod
    def toDict(self) -> dict[str, any]:
        pass

    # Use the given startArgs to initiate the widget.
    @abstractmethod
    def fromDict(self, startArgs: dict[str, any]):
        pass

    # Always call the constructor after the definition of the fields as it will call all 
    # abstract functions and you'll probably will need these definitions for the functions.
    def __init__(self, parent=None, startArgs: dict[str, any] | None = None):
        super().__init__(parent)

        self.parentWindow: Window = parent

        self.widgetLayout = QVBoxLayout(self)
        self.widgetLayout.setContentsMargins(0,0,0,0)
        
        if startArgs is not None:
            self.fromDict(startArgs)
        
        self.setContent(self.widgetLayout)