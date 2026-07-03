"""
Simulated Machine #1: CNC Mill (speaks OPC-UA)

WHY THIS SHAPE:
Real industrial devices expose an OPC-UA "address space" - a tree of
Objects and Variables, like a filesystem. A client (our edge gateway)
connects and reads/subscribes to specific nodes, e.g.
  Objects/CNCMill1/Temperature

We're simulating that tree here, and updating the values every second
to mimic live sensor readings.
"""

import asyncio
import random
from asyncua import Server


async def main():
    # 1. Create the server - this is the "machine" itself
    server = Server()
    await server.init()

    # Every OPC-UA server needs an endpoint - the address a client connects to.
    # Port 4840 is the OPC-UA standard port (like 80 is to HTTP).
    server.set_endpoint("opc.tcp://0.0.0.0:4840/freeopcua/server/")

    # 2. Register a "namespace" - think of it like a company's unique
    # prefix so node names don't collide with other vendors' machines.
    uri = "http://factory-edge.example/cncmill1"
    idx = await server.register_namespace(uri)

    # 3. Build the address space: an Object representing the machine,
    # with Variables under it representing live sensor readings.
    machine_obj = await server.nodes.objects.add_object(idx, "CNCMill1")

    temperature = await machine_obj.add_variable(idx, "Temperature", 20.0)
    vibration = await machine_obj.add_variable(idx, "Vibration", 0.0)
    rpm = await machine_obj.add_variable(idx, "RPM", 0)
    error_code = await machine_obj.add_variable(idx, "ErrorCode", 0)

    # By default OPC-UA variables are read-only to clients unless we
    # explicitly allow writes. Our edge gateway will only ever READ these,
    # so we leave write access off - this mirrors a real PLC.
    for var in (temperature, vibration, rpm, error_code):
        await var.set_writable(False)

    print(f"Starting CNCMill1 OPC-UA server at {server.endpoint}")

    # 4. Run the server and, in a loop, update values to simulate
    # a real machine's sensor drift and occasional faults.
    async with server:
        while True:
            await asyncio.sleep(1)

            # Normal operation: values wobble around a baseline
            new_temp = round(60 + random.uniform(-2, 2), 2)
            new_vib = round(random.uniform(0.1, 0.5), 3)
            new_rpm = random.randint(1400, 1600)

            # Occasionally simulate a fault (5% chance) - useful later
            # for testing our anomaly detection in Phase 3
            fault = random.random() < 0.05
            new_error = 1 if fault else 0
            if fault:
                new_temp += 15  # overheating during fault

            await temperature.write_value(new_temp)
            await vibration.write_value(new_vib)
            await rpm.write_value(new_rpm)
            await error_code.write_value(new_error)

            print(
                f"Temp={new_temp}C  Vib={new_vib}  RPM={new_rpm}  "
                f"Error={new_error}"
            )


if __name__ == "__main__":
    asyncio.run(main())
