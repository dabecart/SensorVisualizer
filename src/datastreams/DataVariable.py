# **************************************************************************************************
# @file DataVariable.py
# @brief When data is parsed from a DataStream, all fields get converted into DataVariables.
#
# @project   SensorVisualizer
# @version   1.0
# @date      2024-09-15
# @author    @dabecart
#
# @license
# This project is licensed under the MIT License - see the LICENSE file for details.
# **************************************************************************************************

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, ClassVar
from collections import deque
from time import time

@dataclass
class DataVariable():
    # A data variable is keyed by its name and source.
    _instances: ClassVar[dict[str, DataVariable]]       = {}

    @staticmethod
    def getVariable(vbeName: str, sourceName: str) -> DataVariable|None:
        keyName: str = DataVariable._generateKeyName(vbeName, sourceName)
        return DataVariable._instances.get(keyName, None)

    _MAX_RECORD_LENGTH: ClassVar[int]                   = 100

    # Name of the variable.
    name:       str|None                                = None
    # Name of the source of this variable.
    source:     str|None                                = None
    # Type of the variable.
    varType:    type|None                               = None
    # The last sent value.
    _value:     any|None                                = None
    # FIFO list with all the last _MAX_RECORD_LENGTH values.
    lastValues: deque[any|None]                         = deque(maxlen=_MAX_RECORD_LENGTH)
    # Store the times the lastValues were received.
    times:      deque[float]                            = deque(maxlen=_MAX_RECORD_LENGTH)
    # List of functions that update the widget associated with this variable.
    hooks:      list[Callable[[DataVariable], None]]    = field(default_factory = lambda: [])

    def __post_init__(self):
        if self.keyName in DataVariable._instances:
            raise Exception(f"There is a duplicated DataVariable: {self.keyName}")

        DataVariable._instances[self.keyName] = self

    @property
    def value(self) -> any|None:
        return self._value
    
    @value.setter
    def value(self, newVal: any|None):
        # Try to cast the new value if (type) is not None.
        if self.source is not None:
            newVal = self.source(newVal)

        # Update values.
        self._value = newVal
        self.lastValues.append(newVal)
        self.times.append(time())

        # Call the hooks.
        for hook in self.hooks:
            hook(self)

    @property
    def keyName(self) -> str:
        return DataVariable._generateKeyName(self.name, self.source)
    
    @staticmethod
    def _generateKeyName(vbeName: str, sourceName: str) -> str:
        return vbeName + "@" + sourceName
    
