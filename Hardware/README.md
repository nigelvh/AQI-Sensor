# AQI Sensor Hardware
This is a custom board for interfacing an ESP32 microcontroller with a pair of Plantower PMS7003 particulate sensors, and a Bosch Sensortec BME280 Temperature, Pressure, and Humidity sensor.

The hardware was designed, along with a 3D printed carrier, to mount inside a 3" PVC pipe cap for a simple and inexpensive outdoor enclosure. It should be noted that the design requires use of a 3" PVC pipe cap with a domed end. The flat face pipe caps will not let the board and carrier seat fully.

## Circuit Board
The schematic and board files have been created in Eagle, though I cannot guarantee how they will load without all of the associated libraries. The gerber files are also provided which can be sent directly to a PCB fab house. Additionally there are exported images of the schematic and board designs for review without using the Eagle CAD software.

A parts text file has been included to cover some of the more important, or more specific, parts used in the design. It is not all inclusive (I didn't include the passives for example), but it covers the main components.

## 3D Print
The board is designed to fit into a 3D printed carrier, and mount into a 3" PVC pipe cap to form the outdoor enclosure. I have printed these in PETG which was chosen for its properties when exposed to the elements. Your choices may differ.

The carrier was modelled in FreeCAD, but the STL has been provided as well to import directly into your slicer of choice.
