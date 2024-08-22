# **************************************************************************************************
# @file Icons.py
# @brief Tools to generate icons from the ResourcePacket.py file and color SVG icons on runtime.
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-08-19
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtGui import QPixmap, QImage, QPainter, QIcon
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, QFile, Qt

# Don't remove this "unused" import, contains the resource images.
import ResourcePacket

class TrackableIcon(QIcon):
    _instances = []

    def __init__(self, filePath, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__class__._instances.append(self)
        self.filePath = filePath

    def setAssociatedWidget(self, associatedWidget: QWidget, width: int|None = None, height: int|None = None):
        self.associatedWidget: QWidget = associatedWidget
        self.width = width
        self.height = height

        # Remove the previously associated widget with this icon.
        instanceToDelete = None
        for ins in self.__class__._instances:
            if not hasattr(ins, 'associatedWidget'):
                continue

            if ins.associatedWidget is not None and ins.associatedWidget is associatedWidget:
                instanceToDelete = ins
                break

        if instanceToDelete is not None and instanceToDelete is not self:
            self.__class__._instances.remove(instanceToDelete)

        # Set the icon on the associated widget.
        if hasattr(self.associatedWidget, 'setIcon'):
            self.associatedWidget.setIcon(self)
        elif hasattr(self.associatedWidget, 'setPixmap'):
            if width is None or height is None:
                raise Exception("Set the width and height on a pixmap associated widget.")
            self.associatedWidget.setPixmap(self.pixmap(width, height))

    def recolor(self, color):
        if not hasattr(self, 'associatedWidget') or self.associatedWidget is None:
            return
        
        self.swap(recolorSVG(self.filePath, color))

        try:
            if hasattr(self.associatedWidget, 'setIcon'):
                self.associatedWidget.setIcon(self)
            elif hasattr(self.associatedWidget, 'setPixmap'):
                if self.associatedWidget.pixmap() is None:
                    return
                self.associatedWidget.setPixmap(self.pixmap(self.width, self.height))
        except:
            # If the icon were to be deleted, it would throw a "wrapped C/C++ object of type x has 
            # been deleted", so remove it in that case.
            self.__class__._instances.remove(self)

    @classmethod
    def recolorAllIcons(cls, theme):
        if theme is None:
            return 
        
        match theme.colorTheme:
            case 'light':
                color = "#4D5157"
            case 'dark':
                color = "#FFF"

        for icon in cls._instances:
            icon.recolor(color)

def createIcon(iconPath: str, theme = None) -> TrackableIcon | QIcon:
    if theme is None:
        return QIcon(iconPath)
    
    if type(theme) is str:
        color: str = theme
    else:
        color: str = theme.colorTheme

    match color:
        case 'light':
            color = "black"
        case 'dark':
            color = "white"
        case _:
            return recolorSVG(iconPath, color)
        
    return TrackableIcon(iconPath, recolorSVG(iconPath, color))

def recolorSVG(icon_path: str, color: str) -> QIcon:
    # Load the SVG data from the resource
    file = QFile(icon_path)
    if not file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
        raise FileNotFoundError(f"SVG file not found: {icon_path}")
    
    try:
        svg_data = file.readAll().data().decode('utf-8')
    except:
        # The file is surely not an SVG.
        file.close()
        return QIcon(icon_path)
    
    file.close()

    # Modify the SVG data to change the fill color
    colored_svg_data = svg_data.replace('fill="#000000"', f'fill="{color}"')
    
    # Convert the modified SVG data to QByteArray
    byte_array = QByteArray()
    buffer = QBuffer(byte_array)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    buffer.write(colored_svg_data.encode('utf-8'))
    buffer.close()

    # Load the modified SVG data into QSvgRenderer
    renderer = QSvgRenderer(byte_array)
    
    # Create a QImage to render the SVG onto
    image = QImage(renderer.defaultSize(), QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)  # Fill with transparency

    # Render the SVG onto the QImage
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()

    # Convert QImage to QPixmap for display
    pixmap = QPixmap.fromImage(image)
    return QIcon(pixmap)