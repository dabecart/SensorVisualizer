# **************************************************************************************************
# @file WidgetLocator.py
# @brief Simple tool to convert from a string to the relevant type. This is used to instantiate 
# classes from the text stored on a save file.
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-09-15
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from widgets.PlotWidget import PlotWidget

def strToWidget(typeName: str) -> type:
    match(typeName):
        case 'PlotWidget': return PlotWidget
        case _: return None