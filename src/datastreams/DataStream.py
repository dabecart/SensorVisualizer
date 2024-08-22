from abc import ABC, abstractmethod
import shlex, os, subprocess
from time import perf_counter
from datetime import datetime
import asyncio

class DataStream(ABC):
    _preprocessor       : str|None   = None

    @property
    def preprocessor(self) -> str|None:
        return self._preprocessor

    @preprocessor.setter
    def preprocessor(self, pythonFile: str|None) -> None:
        self._preprocessor = pythonFile

    # This function should return a string of raw data, which may or may not be already processed.
    @abstractmethod
    def _getInputData(self) -> str|None:
        pass

    async def getDataFields(self) -> dict[str, str]|None:
        # Fetch the input data from the source.
        input: str|None = self._getInputData()

        # No data to process.
        if input is None:
            return None

        # Call the preprocessor if any.
        if self._preprocessor is not None:
            processOutput = await self._executeCommand(self._preprocessor + ' "' + input + '"', None)
            input = processOutput.get("output", input)

        # Parse the input as a dictionary.
        

    def __init__(self) -> None:
        super().__init__()

    async def _executeCommand(self, cmd: str, cwd: str|None) -> dict[str, any]:
        commandArgs = shlex.split(cmd)
        # So that the windowed application doesn't open a terminal to run the code on Windows (nt).
        # Taken from here:
        # https://code.activestate.com/recipes/409002-launching-a-subprocess-without-a-console-window/
        
        tOfExec = datetime.now().strftime("%d/%m/%Y %H:%M:%S.%f")
        if os.name == 'nt':
            startupInfo = subprocess.STARTUPINFO()
            startupInfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            startTime = perf_counter()
            runResult = await subprocess.run(commandArgs,
                                    stdout   = subprocess.PIPE, 
                                    stderr   = subprocess.PIPE,
                                    cwd      = cwd,
                                    startupinfo = startupInfo)
            executionTime = perf_counter() - startTime
        else:
            startTime = perf_counter()
            runResult = await subprocess.run(commandArgs,
                                    stdout   = subprocess.PIPE, 
                                    stderr   = subprocess.PIPE,
                                    cwd      = cwd)
            executionTime = perf_counter() - startTime

        # Taken from here: 
        # https://stackoverflow.com/questions/24849998/how-to-catch-exception-output-from-python-subprocess-check-output
        if runResult.stderr:
            raise subprocess.CalledProcessError(
                returncode = runResult.returncode,
                cmd = runResult.args,
                stderr = runResult.stderr
            )
        
        return {"output"        : runResult.stdout.decode('utf-8'),
                "return"        : runResult.returncode,
                "execDelta"     : executionTime,
                "execTime"      : tOfExec}