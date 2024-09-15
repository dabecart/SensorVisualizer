# **************************************************************************************************
# @file DataListener.py
# @brief Functions running in parallel with the GUI that listens to all DataStreams and parses all
# available variables and updates their values.
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-09-15
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from datastreams.DataStream import DataStream
from datastreams.DataVariable import DataVariable

from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

class DataListener(QObject):
    # Signal to main thread to update the widgets associated with the values coming from the 
    # streams. 
    updateHooks = pyqtSignal(list)
    # Signal emitted when the while loop ends.
    listenerFinished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        while self.running:
            self._processStreams()
            # A necessary evil right here...
            QThread.msleep(10)
        self.listenerFinished.emit()

    @pyqtSlot()
    def stop(self):
        self.running = False

    # TODO: Add functions to initialize and set values for the streams when reading from a file.

    def _processStreams(self):
        updateVbeList: list[tuple[DataVariable, any]] = []

        for streamName, stream in DataStream._instances.items():
            # Find a DataStream with available data.
            if not stream.dataAwaiting():
                continue
                
            print(f"\n\nProcessing {streamName}")
            # Fetch the data from the stream and convert it to a dictionary of variable names and 
            # values.
            inputData: dict[str, any]|None = stream.getDataFields()
            print(f"inputData {inputData}")
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
            print("update list emitted!")
            # Emit the signal only if there are variables to update.
            self.updateHooks.emit(updateVbeList)