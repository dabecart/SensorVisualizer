import serial
from time import sleep
import json

outDict = {
    "name":     "Danotests",
    "variable": 0
}

ser = serial.Serial("COM3")
while True:
    out: str = "{"
    for key, val in outDict.items():
        out += key +": " +str(val) + ", "
    out = out[:-2] + "}"

    out = out.encode('utf-8')
    print(out)
    ser.write(out)

    outDict["variable"] += 1
    sleep(1)