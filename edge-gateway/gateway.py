"""
Edge Gateway - reads from both simulated machines (OPC-UA + Modbus)
and publishes normalized JSON to MQTT.

WHY THIS SHAPE:
This is the core "edge" component in an IIoT architecture. It abstracts
away protocol differences (OPC-UA vs Modbus) so anything downstream -
dashboards, cloud services, anomaly detection - only ever deals with
one consistent JSON format, regardless of which protocol the data
originally came from.

Run opcua_machine.py, modbus_machine.py, and the Mosquitto container
FIRST, then run this.
"""

import asyncio
import json
import time

from asyncua import Client as OpcuaClient
from pymodbus.client import AsyncModbusTcpClient
import paho.mqtt.client as mqtt

import os

OPCUA_URL = os.getenv("OPCUA_URL", "opc.tcp://localhost:4840/freeopcua/server/")
MODBUS_HOST = os.getenv("MODBUS_HOST", "localhost")
MODBUS_PORT = int(os.getenv("MODBUS_PORT", "5020"))
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# Modbus register map - must match modbus_machine.py exactly, since
# Modbus itself carries no field names, only raw register numbers
REG_RPM = 0
REG_TEMP_X10 = 1
REG_FAULT = 2


async def read_opcua(client):
    """Read all sensor values from the CNC Mill via OPC-UA."""
    objects = client.nodes.objects
    machine = await objects.get_child("2:CNCMill1")
    temperature = await machine.get_child("2:Temperature")
    vibration = await machine.get_child("2:Vibration")
    rpm = await machine.get_child("2:RPM")
    error_code = await machine.get_child("2:ErrorCode")

    return {
        "temperature": await temperature.read_value(),
        "vibration": await vibration.read_value(),
        "rpm": await rpm.read_value(),
        "fault": bool(await error_code.read_value()),
    }


async def read_modbus(client):
    """Read all sensor values from the Conveyor Motor via Modbus."""
    result = await client.read_holding_registers(address=0, count=3, slave=1)
    rpm = result.registers[REG_RPM]
    temp = result.registers[REG_TEMP_X10] / 10  # undo the x10 scaling trick
    fault = bool(result.registers[REG_FAULT])

    return {
        "temperature": temp,
        "rpm": rpm,
        "fault": fault,
    }


async def main():
    # 1. Connect to the OPC-UA machine
    opcua_client = OpcuaClient(url=OPCUA_URL)
    await opcua_client.connect()
    print(f"Connected to OPC-UA machine at {OPCUA_URL}")

    # 2. Connect to the Modbus machine
    modbus_client = AsyncModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    await modbus_client.connect()
    print(f"Connected to Modbus machine at {MODBUS_HOST}:{MODBUS_PORT}")

    # 3. Connect to the MQTT broker. paho-mqtt's client is synchronous
    # under the hood, so loop_start() runs its network handling in a
    # background thread - we just call publish() and it queues/sends.
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.connect(MQTT_HOST, MQTT_PORT)
    mqtt_client.loop_start()
    print(f"Connected to MQTT broker at {MQTT_HOST}:{MQTT_PORT}")

    try:
        while True:
            # Read from both machines concurrently - no reason to wait
            # for one before starting the other, they're independent
            cnc_data, conveyor_data = await asyncio.gather(
                read_opcua(opcua_client),
                read_modbus(modbus_client),
            )

            # Stamp every reading with when the GATEWAY captured it.
            # This matters because network/processing delay means
            # "when published" is not the same instant as "when measured" -
            # you'll want this for accurate analysis later.
            timestamp = time.time()
            cnc_data["timestamp"] = timestamp
            conveyor_data["timestamp"] = timestamp

            # One bundled JSON message per machine - both protocols now
            # look identical to anything subscribing downstream
            mqtt_client.publish("factory/cncmill1", json.dumps(cnc_data))
            mqtt_client.publish("factory/conveyor1", json.dumps(conveyor_data))

            print(f"[GATEWAY] cncmill1   -> {cnc_data}")
            print(f"[GATEWAY] conveyor1  -> {conveyor_data}")

            await asyncio.sleep(1)

    finally:
        await opcua_client.disconnect()
        await modbus_client.close()
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())