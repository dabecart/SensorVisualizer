from widgets.PlotWidget import PlotWidget

def strToWidget(typeName: str) -> type:
    match(typeName):
        case 'PlotWidget': return PlotWidget
        case _: return None