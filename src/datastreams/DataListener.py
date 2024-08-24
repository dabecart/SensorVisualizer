from datastreams.DataStream import DataStream
from datastreams.DataVariable import DataVariable
from threading import Event

def dataRoutine(killPill: Event):
    while not killPill.is_set():
        _processStreams()

def _processStreams():
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

            vbeObject.value = vbeValue