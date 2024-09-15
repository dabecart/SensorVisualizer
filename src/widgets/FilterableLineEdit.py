# **************************************************************************************************
# @file FilterableLineEdit.py
# @brief A QLineEdit that lists some predefined options but still lets you write what you want.
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-09-15
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QLineEdit, QCompleter
from PyQt6.QtCore import Qt, QStringListModel

class FilterableLineEdit(QLineEdit):
    def __init__(self, options:list[str]|None = None):
        super().__init__()

        # Set up the completer with the provided options
        self._completer = QCompleter(self)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setModelSorting(QCompleter.ModelSorting.CaseInsensitivelySortedModel)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        # Set the completer on the line edit
        self.setCompleter(self._completer)

        self.setOptions(options)

    def setOptions(self, options: list[str]|None):
        if options is None:
            options = []
        
        self.model = QStringListModel(options, self)
        self._completer.setModel(self.model)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        super().keyPressEvent(a0)

        # Show all options when the text is empty
        if not self.text():
            self._completer.setCompletionPrefix("")
            self._completer.complete()

class FilterableIntLineEdit(FilterableLineEdit):
    def __init__(self, options:list[int]|None =None):
        if options is None:
            super().__init__()
        else:
            super().__init__([str(i) for i in options])

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Allow only digits (0-9) and navigation keys (backspace, delete, arrow keys).
        if event.key() in (
            Qt.Key.Key_0, Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3, 
            Qt.Key.Key_4, Qt.Key.Key_5, Qt.Key.Key_6, Qt.Key.Key_7, 
            Qt.Key.Key_8, Qt.Key.Key_9,
            Qt.Key.Key_Backspace, Qt.Key.Key_Delete,
            Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Home, Qt.Key.Key_End
        ):
            super().keyPressEvent(event)
        else:
            # Ignore any non-numeric and non-navigation key presses.
            event.ignore()

    def setOptions(self, options: list[int] | None):
        if options is None:
            super().setOptions(options)
        else:
            super().setOptions([str(i) for i in options])

    def getInt(self):
        return int(self.text())
