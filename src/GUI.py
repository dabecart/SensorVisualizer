from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, QMenuBar, QTabWidget, QLabel, QWidget, QTabBar, QMenu, QLineEdit, 
)
from PyQt6.QtGui import QAction, QContextMenuEvent, QFocusEvent, QKeyEvent
from PyQt6.QtCore import Qt

from widgets.WindowArea import WindowArea
from widgets.Window import Window

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MDI Application")
        self.setGeometry(100, 100, 800, 600)

        # Needed to trigger the focus out event on the QLineEdits inside the tabbed pane.
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        # Create a QTabWidget with tabs at the bottom
        self.tabWidget = QTabWidget()
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.South)
        self.setCentralWidget(self.tabWidget)

        # Add the initial tab
        self.addNewTab(number=0)

        # Add the "Add New Tab" button as a tab
        self.addTabButton = QLabel()
        self.addTabButton.setText("+")

        index = self.tabWidget.addTab(QWidget(), "")
        self.tabWidget.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, self.addTabButton)

        # Ensures the "+" tab is always at the end
        self.tabWidget.tabBarClicked.connect(self.handleTabClicks)
        self.tabWidget.tabBarDoubleClicked.connect(self.renameTab)

        # Create menu bar.
        self.menu = self.menuBar()

        # Add "Window" menu.
        window_menu = self.menu.addMenu("Window")

        # Add actions to the menu.
        new_action = QAction("New Window", self)
        new_action.triggered.connect(self.createNewSubwindow)
        new_action.setShortcut("Ctrl+N")
        window_menu.addAction(new_action)

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        super().contextMenuPolicy()
        
        index = self.tabWidget.tabBar().tabAt(self.tabWidget.tabBar().mapFromGlobal(event.globalPos()))
        if index >= 0 and index != self.tabWidget.count() - 1:
            menu = QMenu(self)
            deleteAction = menu.addAction("&Delete")
            deleteAction.triggered.connect(lambda: self.deleteTab(index))
            menu.exec(self.tabWidget.mapToGlobal(event.pos()))

    def addNewTab(self, number: int):
        # Increment tab count and create a new widget for the tab.
        newWindowArea = WindowArea()

        # Add the new tab just before the "+" button.
        self.tabWidget.insertTab(self.tabWidget.count() - 1, newWindowArea, f"Tab {number}")

        # Switch to the newly created tab.
        self.tabWidget.setCurrentWidget(newWindowArea)

    def deleteTab(self, index):
        if index != self.tabWidget.count() - 1:
            self.tabWidget.removeTab(index)
            if self.tabWidget.currentIndex() == self.tabWidget.count()-1:
                self.tabWidget.setCurrentIndex(self.tabWidget.count()-2)

    def handleTabClicks(self, index):
        # If the "+" tab is clicked, add a new tab.
        if index == self.tabWidget.count()-1:
            self.addNewTab(self.tabWidget.count()-1)

    def renameTab(self, index):
        if index >= 0 and index != self.tabWidget.count() - 1:
            current_tab_name = self.tabWidget.tabText(index)
            self.line_edit = CurstomLineEdit(current_tab_name)
            self.line_edit.setFrame(False)
            self.tabWidget.setTabText(index, "")
            self.tabWidget.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, self.line_edit)
            self.line_edit.setFocus()
            self.line_edit.editingFinished.connect(lambda: self.finishRenaming(index))

    def finishRenaming(self, index):
        new_name = self.line_edit.text()
        if new_name.strip() == "":
            new_name = f"Tab {index + 1}"
        self.tabWidget.setTabText(index, new_name)
        self.tabWidget.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, None)
        self.line_edit.deleteLater()

    def createNewSubwindow(self):
        # Create a custom subwindow.
        sub_window = Window(self.tabWidget.currentWidget())
        text_edit = QTextEdit()
        sub_window.setWidget(text_edit)
        sub_window.setWindowTitle("Subwindow")

        # Add the subwindow to the window area (the current tab widget).
        self.tabWidget.currentWidget().addSubWindow(sub_window)
        sub_window.show()

class CurstomLineEdit(QLineEdit):
    def __init__(self, text):
        super().__init__(text)
        self.originalText = text
        self.selectAll()

    def focusOutEvent(self, a0: QFocusEvent | None) -> None:
        super().focusOutEvent(a0)
        self.editingFinished.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.setText(self.originalText)
            self.editingFinished.emit()
        else:
            super().keyPressEvent(a0)