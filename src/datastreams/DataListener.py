from datastreams.DataStream import DataStream
from datastreams.DataVariable import DataVariable

from PyQt6.QtCore import QThread, pyqtSignal

class DataListener(QThread):
    # Signal to main thread to update the widgets associated with the values coming from the 
    # streams. 
    updateHooks = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            self._processStreams()
            # A necessary evil right here...
            self.msleep(10)

    def stop(self):
        self.running = False
        # Wait for the loop to finish.
        self.wait() 

    # TODO: Add functions to initialize and set values for the streams when reading from a file.

    def _processStreams(self):
        updateVbeList: list[tuple[DataVariable, any]] = []

        for streamName, stream in DataStream._instances.items():
            # Find a DataStream with available data.
            if not stream.dataAwaiting():
                continue
        
            # Fetch the data from the stream and convert it to a dictionary of variable names and 
            # values.
            inputData: dict[str, any]|None = stream.getDataFields()
            if inputData is None: 
                continue

            # Pass the value to each variable, if the variable object has been created.
            for vbeName, vbeValue in inputData.items():
                vbeObject: DataVariable|None = DataVariable.getVariable(vbeName, streamName)
                if vbeObject is None:
                    # If the variable is not instantiated, skip it.
                    continue
                
                # By setting the vbeObject value, it will update the widget. 
                # The only thing is that this has to be done on the main thread (the thread with the
                # GUI) for it to work properly. For that, emit a signal to the main thread and pass
                # it a list of tuples so that these setters get called.
                updateVbeList.append((vbeObject, vbeValue))

        if updateVbeList:
            # Emit the signal only if there are variables to update.
            self.updateHooks.emit(updateVbeList)