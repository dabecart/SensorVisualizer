# **************************************************************************************************
# @file GUI.py
# @brief The main display of the SensorVisualizer.
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-09-15
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import (
    QMainWindow, QStatusBar, QToolButton, QTabWidget, QLabel, QWidget, QTabBar, QMenu, QLineEdit, 
    QMessageBox, QFileDialog
)
from PyQt6.QtGui import (
    QCloseEvent, QContextMenuEvent, QFocusEvent, QKeyEvent, QFontMetrics, QResizeEvent, QPalette
)
from PyQt6.QtCore import Qt, pyqtSlot, QThread

from widgets.WindowArea import WindowArea
from widgets.Window import Window
from tools.UndoRedo import UndoRedo
from tools.Icons import createThemedIcon, TrackableIcon
from tools.WidgetLocator import strToWidget
from SettingsWindow import ProgramConfig, SettingsWindow
from datastreams.DataListener import DataListener
from datastreams.DataVariable import DataVariable

from dataclasses import asdict
import json

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from widgets.DataWidget import DataWidget

import traceback

class GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensor Visualizer")
        self.setGeometry(100, 100, 800, 600)

        # Stores the configuration of the program.
        self.config = ProgramConfig()
        # Field to save the currently opened file.
        self.currentFile: str|None = None
        # If no action has been done, then it's a blank program.
        self.blankProgram: bool = True

        # Check if the color is closer to black (dark mode) or white (light mode)
        color = self.palette().color(QPalette.ColorRole.Window)
        brightness = (color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114) / 255
        self.config.colorTheme = "dark" if  brightness < 0.5 else "light"

        TrackableIcon.setThemeReference(self.config)

        # Needed to trigger the focus out event on the QLineEdits inside the tabbed pane.
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

        self.createBlankTabWidget()
        # Add the initial tab.
        self.addNewTab(number=0)

        # Create menu bar.
        self.menubar = self.menuBar()

        fileMenu = self.menubar.addMenu('&File')

        openAction = fileMenu.addAction('&Open...')
        openAction.setShortcut("Ctrl+O")
        openAction.setStatusTip("Open a file.")
        openAction.triggered.connect(self.openFile)

        saveAction = fileMenu.addAction('&Save')
        saveAction.setShortcut("Ctrl+S")
        saveAction.setStatusTip("Save the current file.")
        saveAction.triggered.connect(self.saveFile)

        closeFileAction = fileMenu.addAction('&Close file')
        closeFileAction.setShortcut("Ctrl+W")
        closeFileAction.setStatusTip("Close the current file.")
        closeFileAction.triggered.connect(self.closeFile)

        fileMenu.addSeparator()

        quitAction = fileMenu.addAction('&Quit')
        quitAction.setShortcut("Ctrl+Q")
        quitAction.setStatusTip("Quit the application.")
        quitAction.triggered.connect(self.close)

        self.editMenu = self.menubar.addMenu('&Edit')

        # Configure undo/redo.
        UndoRedo.setGUI(self)

        # Set up undo action.
        undoAction = self.editMenu.addAction('&Undo')
        undoAction.setShortcut("Ctrl+Z")
        undoAction.setStatusTip("Undo the last operation.")
        undoAction.triggered.connect(UndoRedo.undo)

        # Set up redo action.
        redoAction = self.editMenu.addAction('&Redo')
        redoAction.setShortcut("Ctrl+Y")
        redoAction.setStatusTip("Redo the last operation.")
        redoAction.triggered.connect(UndoRedo.redo)

        self.editMenu.addSeparator()

        addWidgetMenu = self.editMenu.addMenu('&Add widget')
        addWidgetMenu.menuAction().setStatusTip("Add a new widget.")
        
        addPlotWidgetAction = addWidgetMenu.addAction("&Plot widget")
        addPlotWidgetAction.setStatusTip("Display a widget graph.")
        addWidgetMenu.triggered.connect(lambda: self.runAction('widget-add-PlotWidget', 'undo'))

        removeWidgetAction = self.editMenu.addAction('&Remove widget')
        removeWidgetAction.setShortcut("Del")
        removeWidgetAction.setStatusTip("Remove the selected widget.")
        removeWidgetAction.triggered.connect(lambda: self.runAction('widget-remove', 'undo'))

        duplicateWidgetAction = self.editMenu.addAction('&Duplicate widget')
        duplicateWidgetAction.setShortcut("Alt+D")
        duplicateWidgetAction.setStatusTip("Duplicate the selected widget.")
        duplicateWidgetAction.triggered.connect(lambda: self.runAction('widget-duplicate', 'undo'))

        self.editMenu.addSeparator()

        projectSettings = self.editMenu.addAction('&Project settings')
        projectSettings.setShortcut("Alt+.")
        projectSettings.setStatusTip("Set the project and test configuration.")
        projectSettings.triggered.connect(lambda: self.runAction('change-project-settings', 'undo'))

        settingsMenu = self.menubar.addMenu('&Settings')
        programSettAction = settingsMenu.addAction('&Program settings')
        programSettAction.setShortcut("Ctrl+R")
        programSettAction.setStatusTip("Configure the program behavior.")
        programSettAction.triggered.connect(lambda: self.runAction('change-program-settings', 'undo'))

        helpMenu = self.menubar.addMenu('&Help')
        aboutAction = helpMenu.addAction('&About')
        aboutAction.setShortcut("F1")
        aboutAction.setStatusTip("Get help and info about this program.")
        # TODO: Do the help menu.
        aboutAction.triggered.connect(lambda: print("TODO: Show the HELP menu!"))

        # Tool bars!
        widgetToolBar = self.addToolBar('Widget')
        widgetToolBar.setMovable(False)
        addWidgetToolBarButton = QToolButton()
        addWidgetToolBarButton.setMenu(addWidgetMenu)
        addWidgetToolBarButton.setStatusTip(addWidgetMenu.menuAction().statusTip())
        addWidgetToolBarButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        widgetToolBar.addWidget(addWidgetToolBarButton)

        fileToolBar = self.addToolBar('File')
        fileToolBar.setMovable(False)
        fileToolBar.addAction(openAction)
        fileToolBar.addAction(saveAction)

        editToolBar = self.addToolBar('Edit')
        editToolBar.setMovable(False)
        editToolBar.addAction(undoAction)
        editToolBar.addAction(redoAction)

        settingsToolBar = self.addToolBar('Settings')
        settingsToolBar.setObjectName('Settings Toolbar')
        settingsToolBar.setMovable(False)
        settingsToolBar.addAction(projectSettings)
        settingsToolBar.addAction(programSettAction)

        # Add icons to all actions.
        actionsIcons = [
            [openAction,            ':file-open'        ],
            [saveAction,            ':file-save'        ],
            [quitAction,            ':quit'             ],
            [undoAction,            ':edit-undo'        ],
            [redoAction,            ':edit-redo'        ],
            [projectSettings,       ':edit-settings'    ],   
            [addWidgetMenu,         ':widget-add'       ],
            [addWidgetToolBarButton,':widget-add'       ],
            [removeWidgetAction,    ':widget-remove'    ],    
            [duplicateWidgetAction, ':widget-duplicate' ],
            [programSettAction,     ':settings-program' ],    
            [aboutAction,           ':help-about'       ],
        ]

        # Create the icons and set them to the actions. These icons will automatically update during
        # a color theme change.
        for act in actionsIcons:
            createThemedIcon(act[1]).setAssociatedWidget(act[0])

        # Bottom status bar
        self.statusBar : QStatusBar = self.statusBar()
        self.statusBar.showMessage("Ready.", 3000)
        self.statusBarPermanent = QLabel("")
        self.statusBar.addPermanentWidget(self.statusBarPermanent)

        # Initialize the DataListener thread.
        self.dataListenerThread = QThread()
        self.dataListener = DataListener()
        self.dataListener.moveToThread(self.dataListenerThread)
        
        self.dataListenerThread.started.connect(self.dataListener.run)

        self.dataListener.listenerFinished.connect(self.dataListener.deleteLater)
        self.dataListener.listenerFinished.connect(self.dataListenerThread.quit)
        self.dataListener.listenerFinished.connect(self.dataListenerThread.deleteLater)

        self.dataListener.updateHooks.connect(self.runWidgetHooks)
        
        self.dataListenerThread.start()

    @pyqtSlot(list)
    def runWidgetHooks(self, updateVbeList: list[tuple[DataVariable, any]]):
        for vbe, value in updateVbeList:
            vbe.value = value

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.dataListener.stop()
        return super().closeEvent(a0)

    def createBlankTabWidget(self):
        if hasattr(self, 'tabWidget'):
            # If the tabWidget already exists, clear it.
            self.tabWidget.clear()
            # This will delete the tab widget.
            self.tabWidget.setParent(None)

        # Create a QTabWidget with tabs at the bottom.
        self.tabWidget = QTabWidget()
        self.tabWidget.setTabPosition(QTabWidget.TabPosition.South)
        self.setCentralWidget(self.tabWidget)

        # Add the "Add New Tab" button as a tab.
        self.addTabButton = QLabel()
        addTabButtonIcon = createThemedIcon(':tab-add')
        addTabButtonIcon.setAssociatedWidget(self.addTabButton, 15, 15)

        index = self.tabWidget.addTab(QWidget(), None)
        self.tabWidget.tabBar().setTabButton(index, QTabBar.ButtonPosition.LeftSide, self.addTabButton)
        # Ensures the "+" tab is always at the end
        self.tabWidget.tabBarClicked.connect(self.handleTabClicks)
        self.tabWidget.tabBarDoubleClicked.connect(self.renameTab)

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        super().contextMenuEvent(event)
        
        index = self.tabWidget.tabBar().tabAt(self.tabWidget.tabBar().mapFromGlobal(event.globalPos()))
        if index >= 0 and index != self.tabWidget.count() - 1:
            menu = QMenu(self)
            deleteAction = menu.addAction("&Delete")
            deleteAction.triggered.connect(lambda: self.deleteTab(index))
            menu.exec(event.globalPos())

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
            self.runAction('tab-add', 'undo', self.tabWidget.count()-1)

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

    def openFile(self):
        if not self.blankProgram and not self._isFileSaved():
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                self.saveFile()

        fileName, _ = QFileDialog.getOpenFileName(self, 'Open File', '', 'Sensor Visualizer Files (*.sv)')
        if not fileName:
            # Dialog was closed.
            return 
        
        try:
            self.createBlankTabWidget()

            # Quick fix so that the "Open" icon changes with the theme upon opening a file with 
            # different color theme as the current one.
            TrackableIcon._disableIconDeletion = True

            with open(fileName, 'r') as inputFile:
                inputDict: dict[str,any] = json.load(inputFile)
                self._fromDict(inputDict)

            TrackableIcon._disableIconDeletion = False

            self.currentFile = fileName
            self.statusBar.showMessage("File opened.", 3000)
        except:
            # Clear all if failed.
            self.createBlankTabWidget()
            self.addNewTab(number=0)
            QMessageBox.critical(self, 'Error while opening', f'Could not open file.\n{traceback.format_exc()}')

    def saveFile(self):
        if not self.currentFile:
            fileName, _ = QFileDialog.getSaveFileName(self, 'Save New File', '', 'Sensor Visualizer Files (*.sv)')
            if fileName:
                self.currentFile = fileName
            else:
                return

        try:
            with open(self.currentFile, 'w') as file:
                json.dump(self._toDict(), file)

            self.statusBar.showMessage("File saved.", 3000)
        except:
            QMessageBox.critical(self, 'Error while saving', f'Could not save.\n{traceback.format_exc()}')

    def closeFile(self):
        if self.blankProgram:
            return

        if not self.currentFile or not self._isFileSaved():
            reply = QMessageBox.question(self, 'Unsaved Changes',
                                         'You have unsaved changes. Do you want to save them?',
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                                         QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Yes:
                if not self.saveFile():
                    return
        
        self.currentFile = None
        self.blankProgram = True
        UndoRedo.clear()
        
        # Restart the interface.
        self.createBlankTabWidget()
        self.addNewTab(number=0)
        self.statusBar.showMessage("File closed.", 3000)

    def _isFileSaved(self) -> bool:
        if self.currentFile is None:
            return False

        currentFile = json.dumps(self._toDict())
        with open(self.currentFile, 'r') as saveFile:
            return currentFile == saveFile.read()

    def _fromDict(self, inputDict: dict[str, any]):
        tabList: list[dict[str, any]] = inputDict.get("tabs", [])
        # For every tab...
        for tabNumber, tab in enumerate(tabList):
            self.addNewTab(tabNumber)
            # ... set the tab name ...
            self.tabWidget.setTabText(tabNumber, tab["tabName"])
            # ... and add its windows.
            for window in tab["windows"]:
                self.runAction("widget-add", None, window)

        self.tabWidget.setCurrentIndex(inputDict.get("selectedTab", 0))

        for configField, configFieldValue in inputDict.get("config", {}).items():
            setattr(self.config, configField, configFieldValue)
        SettingsWindow.applyTheme(self.config)

    def _toDict(self) -> dict[str, any]:
        tabList: list[dict[str, any]] = []
        for i in range(self.tabWidget.count() - 1):
            windowArea: WindowArea = self.tabWidget.widget(i)
            tabList.append({
                "tabName"   :   self.tabWidget.tabText(i),
                "windows"   :   [window.toDict() for window in windowArea.subWindowList()]
            })
        
        return {
            "selectedTab"   : self.tabWidget.currentIndex(),
            "config"        : asdict(self.config),
            "tabs"          : tabList
        }

    def runAction(self, action: str, actionStack: str, *args):
        self.blankProgram = False

        if action == 'change-program-settings':
            settingsWindow = SettingsWindow(self.config, self)
            settingsWindow.exec()
        elif action.startswith('widget-add'):
            # Create a new window that will contain the widget.
            window = Window(self.tabWidget.currentWidget())

            if len(args) >= 1 and type(args[0]) is dict:
                # A dictionary is being passed to initialize the widget.
                window.fromDict(args[0])
            else:
                # Create a "default" widget.
                widgetType: str = action[len('widget-add-'):]
                widgetType: DataWidget = strToWidget(widgetType)
                widget = widgetType(parent=window)
                window.setWidget(widget)
                window.setWindowTitle(widget.parentWindowName)

            # Add the subwindow to the window area (the current tab widget).
            self.tabWidget.currentWidget().addSubWindow(window)
            window.show()
        elif action == 'tab-add':
            self.addNewTab(args[0])
        else:
            print(f"Action {action} not implemented on runAction in GUI.py")

# This line gets positioned on the tab name when it's double clicked to substitute its value.
class CurstomLineEdit(QLineEdit):
    def __init__(self, text):
        super().__init__(text)
        self.originalText = text
        self.selectAll()

        self.textChanged.connect(self.setWidthToContent)
        self.setMinimumWidth(25)

    def setWidthToContent(self):
        font_metrics = QFontMetrics(self.font())
        text_width = font_metrics.horizontalAdvance(self.text()) + 20
        self.setFixedWidth(text_width)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        self.setWidthToContent()
    
    def focusOutEvent(self, a0: QFocusEvent | None) -> None:
        super().focusOutEvent(a0)
        self.editingFinished.emit()

    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_Escape:
            self.setText(self.originalText)
            self.editingFinished.emit()
        else:
            super().keyPressEvent(a0)