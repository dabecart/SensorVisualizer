from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QLineEdit, QCompleter
from PyQt6.QtCore import Qt, QStringListModel

class FilterableLineEdit(QLineEdit):
    def __init__(self, options=None):
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
        
        self.setDisabled(not options)
            
        self.model = QStringListModel(options, self)
        self._completer.setModel(self.model)

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        super().keyPressEvent(a0)

        # Show all options when the text is empty
        if not self.text():
            self._completer.setCompletionPrefix("")
            self._completer.complete()