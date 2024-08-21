from PyQt6.QtWidgets import QMdiSubWindow
from PyQt6.QtCore import Qt, QRect, QLine, QSize, QEvent
from PyQt6.QtGui import QContextMenuEvent, QResizeEvent, QMouseEvent, QMoveEvent, QEnterEvent
from widgets.WindowArea import WindowArea
from widgets.DataWidget import DataWidget
from tools.WidgetLocator import strToWidget

class Window(QMdiSubWindow):
    def __init__(self, mdiArea: WindowArea):
        super().__init__()
        self.mdiArea:       WindowArea = mdiArea

        self.closing:       bool = False
        self.beingResized:  bool = False
        self.beingMoved:    bool = False
        self.mouseClicked:  bool = False
        self.enableEvents:  bool = True

        self.previousSize: QSize = self.size()

        self.resize(200, 200)

        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint)
        self.onHoverFlags = self.windowFlags()
        self.onNotHoverFlags = self.windowFlags() | Qt.WindowType.FramelessWindowHint
        self.setWindowFlags(self.onNotHoverFlags)

    def contextMenuEvent(self, event: QContextMenuEvent | None) -> None:
        # It's giving errors on right clicking the top pane. This fixes it :)
        pass

    def enterEvent(self, event: QEnterEvent | None) -> None:
        super().enterEvent(event)
        if self.closing or (self.windowState() & Qt.WindowState.WindowMinimized): return

        # Show the title bar when the mouse enters the subwindow
        self.setWindowFlags(self.onHoverFlags)

    def leaveEvent(self, event: QEvent | None) -> None:
        super().leaveEvent(event)
        # If the window is being closed or is minimized, don't change the window top bar.
        if self.closing or (self.windowState() & Qt.WindowState.WindowMinimized) : return

        # Hide the title bar when the mouse leaves the subwindow
        self.setWindowFlags(self.onNotHoverFlags)

    def closeEvent(self, event):
        # Disable the leaveEvent while closing.
        self.closing = True
        event.accept()

    def changeEvent(self, event):
        super().changeEvent(event)
        # Handle minimize event by checking if the window state has changed
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                # On minimize, reenable the window frame to allow for resizing to previous size.
                self.setWindowFlags(self.onHoverFlags)

    def mousePressEvent(self, event: QMouseEvent):
        self.previousSize: QSize = self.size()
        super().mousePressEvent(event)
        self.mouseClicked = True

    def mouseReleaseEvent(self, event: QMouseEvent):
        super().mouseReleaseEvent(event)
        self.mouseClicked = False
        self.beingMoved = False
        self.beingResized = False
        self.enableEvents = True
        self.mdiArea.setHintLines([])

    def mouseMoveEvent(self, mouseEvent: QMouseEvent):
        super().mouseMoveEvent(mouseEvent)
        self.enableEvents = True

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)

        # Every time the mouse enters on the window triggers a resizeEvent. We're not interested on
        # those events. Same if the sizes are the same.
        if not self.mouseClicked or self.beingMoved \
           or not self.enableEvents or event.size() == event.oldSize(): 
            return
        
        # print(f"Resizing: {event.oldSize()} -> {event.size()}  {event.size() == event.oldSize()}")

        # Disable events until the mouse moves again. This is because the setGeometry method down 
        # bellow triggers this event again, causing an infinite loop.
        self.enableEvents = False
        self.beingResized = True
        currentRect: QRect = self.resizeHint()

        # TODO: Set the limits.

        self.setGeometry(currentRect)
        self.previousSize = self.size()

    def moveEvent(self, event: QMoveEvent):
        super().moveEvent(event)

        # Every time the mouse enters on the window triggers a moveEvent. We're not interested on
        # those events. Same if the positions are the same.
        # If the current size is not the same as the previous one, then the window is being resized 
        # either from the top or the left side, therefore changing its position, but in reality,
        # it's their size what's being changed.
        if not self.mouseClicked or self.beingResized \
           or not self.enableEvents or event.pos() == event.oldPos() \
           or self.previousSize != self.size(): 
            return
        
        # print(f"Moving: {event.oldPos()} -> {event.pos()}")

        # Disable events until the mouse moves again. This is because the setGeometry method down 
        # bellow triggers this event again, causing an infinite loop.
        self.enableEvents = False
        self.beingMoved = True
        currentRect: QRect = self.preventOverlapping() or self.geometry()

        # TODO: Set the limits.
        if currentRect.left() < 0:
            currentRect.moveLeft(0)
        if currentRect.top() < 0:
            currentRect.moveTop(0)

        self.setGeometry(currentRect)

    def preventOverlapping(self):
        # Get the geometry of the current subwindow
        currentRect: QRect = self.geometry()

        # Pixels within which snapping occurs
        snapThreshold = 20  

        def distanceBetweenSubwindows(a: QMdiSubWindow, b: QMdiSubWindow):
            displacement = a.geometry().center() - b.geometry().center()
            return displacement.manhattanLength()

        # Iterate through all subwindows and find the one that is closer to the moving window.
        hoveringWindow = None
        minDistance = None
        for subwindow in self.mdiArea.subWindowList():
            if subwindow is not self:
                distance = distanceBetweenSubwindows(self, subwindow)
                if hoveringWindow is None or distance < minDistance:
                    hoveringWindow = subwindow
                    minDistance = distance

        if hoveringWindow is None:
            return

        # Get the geometry of the other subwindows.
        otherRect: QRect = hoveringWindow.geometry()

        # Check if the current window overlaps with another window.
        if not currentRect.intersects(otherRect):
            self.mdiArea.setHintLines([])
            return currentRect
        
        """
        On overlap, the window can be fixed to the following positions.
        * means the position is free but cannot overlap the box, so it will "slide" over it.
        The length of the fixed places are given by:
            x Corners are corner positions +- 1/4*(width in X, height in Y)
            x Centered positions are center +- snapThreshold

            top  |   |  top  |    |  top       
    left corner  |   |       |    |  right corner
            =========================
        ____|    ****        ****   |_____
            |*                     *|
            |*                     *|
      ------|                       |------
       left |           x           | right
      ------|                       |------
            |*                     *|
        ____|*                     *|_____
            |    ****        ****   |                   
            =========================
        bottom  |    |      |    |  bottom
    left corner  |    |  bot |    |  left corner
        """
        
        dX: int = otherRect.center().x() - currentRect.center().x()
        dY: int = otherRect.center().y() - currentRect.center().y()
        
        def moveVertical():
            if dY > 0:
                # Move up: the bottom side must be above the top side of the other rectangle.
                currentRect.moveBottom(otherRect.top() - 1)
            elif dY < 0:
                # Move down: the top side must be below the bottom side of the other rectangle.
                currentRect.moveTop(otherRect.bottom() + 1)

        def moveHorizontal():
            if dX > 0:
                # Move left: the right side must be to the left of the left side of the other
                # rectangle.
                currentRect.moveRight(otherRect.left() - 1)
            elif dX < 0:
                # Move right: the left side must be to the right of the right side of the other
                # rectangle.
                currentRect.moveLeft(otherRect.right() + 1)


        hintResizeLinesList: list[QLine] = []

        # 3/4 here are a 1/4 from the corner (take in account we're using the centers position, 
        # not the real corners).
        if abs(dX) > otherRect.width()*3/4 and abs(dY) > otherRect.height()*3/4:
            # Position on the diagonals.
            moveHorizontal()
            moveVertical()
            hintResizeLinesList.append(QLine(currentRect.center(), otherRect.center()))
        elif abs(dX) >= abs(dY):
            # Left-right.
            moveHorizontal()
            # Center horizontally (along X axis).
            if abs(dY) < snapThreshold/2:
                alignedCenter = currentRect.center()
                alignedCenter.setY(otherRect.center().y())
                currentRect.moveCenter(alignedCenter)
                hintResizeLinesList.append(QLine(currentRect.center(), otherRect.center()))
        else:
            # Top-bottom.
            moveVertical()
            # Center vertically (along Y axis).
            if abs(dX) < snapThreshold/2:
                alignedCenter = currentRect.center()
                alignedCenter.setX(otherRect.center().x())
                currentRect.moveCenter(alignedCenter)
                hintResizeLinesList.append(QLine(currentRect.center(), otherRect.center()))

        self.mdiArea.setHintLines(hintResizeLinesList)

        return currentRect

    def resizeHint(self):
        # Pixels within which snapping occurs
        snapThreshold = 10  
        currentRect: QRect = self.geometry()

        # rectA is the one being resized.
        def addHintLines(rectA: QRect, rectB: QRect):
            hintResizeLinesList: list[QLine] = []
            if rectA.left() == rectB.left() or rectA.left() == rectB.right():
                x = rectA.left()

                corners = (rectA.top(), rectA.bottom(), rectB.top(), rectB.bottom())
                minY = min(corners)
                maxY = max(corners)

                hintResizeLinesList.append(QLine(x, minY, x, maxY))

            if rectA.right() == rectB.right() or rectA.right() == rectB.left():
                x = rectA.right() + 1

                corners = (rectA.top(), rectA.bottom(), rectB.top(), rectB.bottom())
                minY = min(corners)
                maxY = max(corners)

                hintResizeLinesList.append(QLine(x, minY, x, maxY))
            
            if rectA.top() == rectB.top() or rectA.top() == rectB.bottom():
                y = rectA.top()

                corners = (rectA.left(), rectA.right(), rectB.left(), rectB.right())
                minX = min(corners)
                maxX = max(corners)

                hintResizeLinesList.append(QLine(minX, y, maxX, y))

            if rectA.bottom() == rectB.bottom() or rectA.bottom() == rectB.top():
                y = rectA.bottom() + 1

                corners = (rectA.left(), rectA.right(), rectB.left(), rectB.right())
                minX = min(corners)
                maxX = max(corners)

                hintResizeLinesList.append(QLine(minX, y, maxX, y))

            return hintResizeLinesList

        # Returns the number of hints found.
        def calculateHintOnBorders(otherRect: QRect) -> list[QLine]:
            notFoundHints = 0
            if abs(currentRect.right() - otherRect.right()) <= snapThreshold:
                currentRect.setRight(otherRect.right())
            elif abs(currentRect.right() - otherRect.left()) <= snapThreshold:
                currentRect.setRight(otherRect.left())
            else:
                notFoundHints += 1
            
            if abs(currentRect.left() - otherRect.left()) <= snapThreshold:
                currentRect.setLeft(otherRect.left())
            elif abs(currentRect.left() - otherRect.right()) <= snapThreshold:
                currentRect.setLeft(otherRect.right())
            else:
                notFoundHints += 1

            if abs(currentRect.bottom() - otherRect.bottom()) <= snapThreshold:
                currentRect.setBottom(otherRect.bottom())
            elif abs(currentRect.bottom() - otherRect.top()) <= snapThreshold:
                currentRect.setBottom(otherRect.top())
            else:
                notFoundHints += 1
            
            if abs(currentRect.top() - otherRect.top()) <= snapThreshold:
                currentRect.setTop(otherRect.top())
            elif abs(currentRect.top() - otherRect.bottom()) <= snapThreshold:
                currentRect.setTop(otherRect.bottom())
            else:
                notFoundHints += 1

            return addHintLines(currentRect, otherRect)


        foundHints: list[QLine] = []
        # Check proximity of edges for snapping (resize hint).
        for subwindow in self.mdiArea.subWindowList():
            if subwindow is self:
                continue
        
            otherRect: QRect = subwindow.geometry()
            foundHints.extend(calculateHintOnBorders(otherRect))

        # Set the resize hints.
        self.mdiArea.setHintLines(foundHints)

        return currentRect
    
    # Convert the window properties and its content to a dictionary.
    def toDict(self) -> dict[str, any]:
        rect = self.geometry()
        return {
            "x"         : rect.x(),
            "y"         : rect.y(),
            "w"         : rect.width(),
            "h"         : rect.height(),
            "type"      : type(self.widget()).__name__,
            "args"      : self.widget().toDict() if type(self.widget()) is DataWidget else None
        }

    # Initialize the window properties and its content from a dictionary.
    def fromDict(self, startArgs: dict[str, any]):
        rect = QRect(   
            startArgs["x"],
            startArgs["y"],
            startArgs["w"],
            startArgs["h"]
        )
        self.setGeometry(rect)

        if startArgs["type"] is None:
            return
        
        # This "converts" from str to type, so then it can be instantiated.
        widgetType: DataWidget = strToWidget(startArgs["type"])
        widget = widgetType(parent=self, startArgs=startArgs["args"])
        self.setWidget(widget)
        self.setWindowTitle(widget.parentWindowName)