import asyncio
from bleak import BleakClient, BleakError, BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection
import time
from .Utils import bytes_to_int, int_to_bytes, crc16_modbus
import binascii

WRITE_SERVICE_UUID = "0000ffd1-0000-1000-8000-00805f9b34fb"
NOTIFY_SERVICE_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

waiting = False
waitStart = 0
waitTimeout = 10
gotReturnVal = False
returnVal = None

batteryRegisterInfo = {
    "cell1Voltage": {
        "description": "Cell 1 voltage",
        "register": 5001,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "cell2Voltage": {
        "description": "Cell 2 voltage",
        "register": 5002,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "cell3Voltage": {
        "description": "Cell 3 voltage",
        "register": 5003,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "cell4Voltage": {
        "description": "Cell 4 voltage",
        "register": 5004,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "cell1Temperature": {
        "description": "Cell 1 Temperature",
        "register": 5018,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "cell2Temperature": {
        "description": "Cell 2 Temperature",
        "register": 5019,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "cell3Temperature": {
        "description": "Cell 3 Temperature",
        "register": 5020,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "cell4Temperature": {
        "description": "Cell 4 Temperature",
        "register": 5021,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "remainingCapacity": {
        "description": "Remain capacity",
        "register": 5044,
        "wordSize": 2,
        "multiplier": 0.001,
    },
    "totalCapacity": {
        "description": "Total capacity",
        "register": 5046,
        "wordSize": 2,
        "multiplier": 0.001,
    },
    "current": {
        "description": "Current",
        "register": 5042,
        "wordSize": 1,
        "multiplier": 0.01,
    },
    "voltage": {
        "description": "Voltage",
        "register": 5043,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "cycleCount": {
        "description": "Cycle count",
        "register": 5048,
        "wordSize": 1,
        "multiplier": 1,
    },
    "dischargeCurentLimit": {
        "description": "Discharge Current Limit",
        "register": 5052,
        "wordSize": 1,
        "multiplier": 0.01,
    },
    "chargeCurentLimit": {
        "description": "Charge Current Limit",
        "register": 5051,
        "wordSize": 1,
        "multiplier": 0.01,
    },
}

# batteryList = [48, 49]

# controllerList = [97]

controllerRegisterInfo = {
    "alternatorVoltage": {
        "description": "Alternator Voltage",
        "register": 0x104,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "alternatorCurrent": {
        "description": "Alternator Current",
        "register": 0x105,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "alternatorPower": {
        "description": "Alternator Power",
        "register": 0x106,
        "wordSize": 1,
        "multiplier": 1,
    },
    "solarVoltage": {
        "description": "Solar Voltage",
        "register": 0x107,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "solarCurrent": {
        "description": "Solar Current",
        "register": 0x108,
        "wordSize": 1,
        "multiplier": 0.1,
    },
    "solarPower": {
        "description": "Solar Power",
        "register": 0x109,
        "wordSize": 1,
        "multiplier": 1,
    },
}


def notification_handler(sender: BleakGATTCharacteristic, data: bytearray):
    global returnVal
    global gotReturnVal
    # print("Wooo got something")
    id = data[0]
    mode = data[1]
    length = data[2]
    start = 3
    end = 3 + length
    val = int.from_bytes(data[start:end], byteorder="big", signed=True)
    # print(data[3:7].hex())
    # print(id, mode, length, val/1000)
    # print(data.hex())
    # print(f"{sender}: {data}")
    returnVal = val
    # print(returnVal)
    gotReturnVal = True
    # exit(0)


async def getStats(
    client: BleakClient, batteryList: list, controllerList: list
) -> dict:
    # print("In device.py!!", client)
    # print(f"Connected: {client.is_connected}")
    # print(batteryList)

    def create_generic_read_request(device_id, function, regAddr, readWrd):
        data = None
        if regAddr != None and readWrd != None:
            data = []
            data.append(device_id)
            data.append(function)
            data.append(int_to_bytes(regAddr, 0))
            data.append(int_to_bytes(regAddr, 1))
            data.append(int_to_bytes(readWrd, 0))
            data.append(int_to_bytes(readWrd, 1))

            crc = crc16_modbus(bytes(data))
            data.append(crc[0])
            data.append(crc[1])
            # logging.debug("{} {} => {}".format("create_request_payload", regAddr, data))
        return data

    async def get_modbus_value(device_id, regAddr, wordLen, multiplier):
        global returnVal
        global gotReturnVal
        writeData = bytes(create_generic_read_request(device_id, 3, regAddr, wordLen))
        waitStart = time.time()
        gotReturnVal = False
        # print(f"About to send: {writeData.hex()}")
        await client.write_gatt_char(WRITE_SERVICE_UUID, writeData, response=True)
        # while (waitStart < time.time() - waitTimeout) and gotReturnVal == False:
        while gotReturnVal == False:
            # print(waitStart, time.time() - waitTimeout, time.time(), waitTimeout, returnVal, gotReturnVal)
            # print("Waiting")
            await asyncio.sleep(0.01)
        #     time.sleep(1)
        # print(f"Got: {returnVal} for dev: {device_id}, reg: {regAddr}")
        return "%.3f" % (returnVal * multiplier)

    await client.start_notify(NOTIFY_SERVICE_UUID, notification_handler)
    # print("To send:", bytes(writeData).hex())
    MODEL_NBR_UUID = "00002a24-0000-1000-8000-00805f9b34fb"
    model_number = await client.read_gatt_char(MODEL_NBR_UUID)
    # print("Model Number: {0}".format("".join(map(chr, model_number))))

    READ_UUID = "0000ffd4-0000-1000-8000-00805f9b34fb"
    # READ_UUID = NOTIFY_SERVICE_UUID
    # ba = await client.read_gatt_char(READ_UUID)
    # print(await get_modbus_value(48, 5044, 2))
    # print(await get_modbus_value(49, 5044, 2))
    retList = {}
    for battery in batteryList:
        batteryDict = {"address": battery, "type": "battery"}
        # print(f"Battery: {battery}")
        for k, v in batteryRegisterInfo.items():
            # print(k, v.get("register"))
            modbusValue = await get_modbus_value(
                battery,
                v.get("register"),
                v.get("wordSize"),
                v.get("multiplier", 1),
            )
            # print(f"{k}: {modbusValue}")
            batteryDict[k] = modbusValue
        retList[battery] = batteryDict

    for controller in controllerList:
        controllerDict = {"address": controller, "type": "controller"}

        # print(f"Controller: {controller}")
        for k, v in controllerRegisterInfo.items():
            # print(k, v.get("register"))
            modbusValue = await get_modbus_value(
                controller, v.get("register"), v.get("wordSize"), v.get("multiplier", 1)
            )
            # print(f"{k}: {modbusValue}")
            controllerDict[k] = modbusValue
        retList[controller] = controllerDict
    # print(retList)
    await client.disconnect()
    return retList
