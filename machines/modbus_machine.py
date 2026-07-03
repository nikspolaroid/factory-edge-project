"""
Simulated Machine #2: Conveyor Belt Motor (speaks Modbus TCP)

WHY THIS SHAPE:
Modbus has no concept of "named" data - just numbered holding registers,
each storing a plain integer (0-65535). There's no built-in way to know
what register 0 "means" - that mapping lives in a separate document
(often literally a PDF or Excel sheet from the vendor).

Our register map for this machine (we're inventing it, like a vendor would):
  Register 0: RPM              (0-3000)
  Register 1: Temperature * 10 (Modbus can't do decimals, so we scale
                                 e.g. 455 means 45.5C - a very common
                                 real-world workaround)
  Register 2: Fault flag        (0 = ok, 1 = fault)

Note: no authentication, no encryption. Anyone who can reach this port
can read AND write these registers. This is exactly why Modbus devices
are a classic OT security weak point - keep this in mind for Phase 4.
"""

import asyncio
import random
import logging

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncTcpServer

logging.basicConfig(level=logging.WARNING)  # keep pymodbus's internal logs quiet


REG_RPM = 0
REG_TEMP_X10 = 1
REG_FAULT = 2


async def update_registers(context):
    """Background task that mutates register values to simulate a live motor."""
    slave_id = 0x00
    while True:
        await asyncio.sleep(1)

        rpm = random.randint(800, 1200)
        temp = round(35 + random.uniform(-2, 2), 1)
        fault = random.random() < 0.05
        if fault:
            temp += 20  # overheating fault

        temp_x10 = int(temp * 10)  # scale to integer, Modbus-friendly

        context[slave_id].setValues(3, REG_RPM, [rpm])
        context[slave_id].setValues(3, REG_TEMP_X10, [temp_x10])
        context[slave_id].setValues(3, REG_FAULT, [1 if fault else 0])

        print(
            f"[MODBUS] RPM={rpm}  Temp={temp}C  "
            f"Fault={1 if fault else 0}"
        )


async def main():
    store = ModbusSlaveContext(
        hr=ModbusSequentialDataBlock(0, [0] * 10)
    )
    context = ModbusServerContext(slaves=store, single=True)

    print("Starting Conveyor Belt Motor (Modbus TCP) on port 5020")
    print("Register map: 0=RPM  1=Temp*10  2=FaultFlag")

    updater_task = asyncio.create_task(update_registers(context))

    await StartAsyncTcpServer(context=context, address=("0.0.0.0", 5020))

    await updater_task


if __name__ == "__main__":
    asyncio.run(main())