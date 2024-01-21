# home-assistant_renogy
A custom home assistant component to poll Renogy BT-2 device connected to a DCDC-30 and Batteries over RS485.

## Installation
Copy the custom_components/renogy to [config dir]/custom_componenets/renogy

## Configuration
Add integration through the intergrations UI in home assistant.
Paramenters:
|Config Parameter|Description|
|---|---|
|Name           |A Friendly name that the device will be known as|
|MAC            |The MAC address of the BT2 deveice|
|Battery IDs    |A comma sperated list of the modbus IDs of your batteries (ommit the comma if only 1)|
|Controller IDs |A comma sperated list of the modbus IDs of your controllers (ommit the comma if only 1)

I can't remember how I found the Modbus IDs of my devices, please raise an issue if you can offer advice for others to follow.

## Sources
I used these sources to help get started with development. Some methods have been reused from these projects.

https://github.com/cyrils/renogy-bt

https://github.com/Olen/solar-monitor/
