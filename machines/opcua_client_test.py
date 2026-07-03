"""
OPC-UA Client - connects to CNCMill1 and reads its live data.

This is the same connection pattern your edge gateway will use in Phase 2,
just without the MQTT forwarding step yet. Run opcua_machine.py FIRST,
then run this in a second terminal.
"""

import asyncio
from asyncua import Client


async def main():
    url = "opc.tcp://localhost:4840/freeopcua/server/"

    # `async with` handles connect + disconnect automatically, even
    # if an error happens mid-read - important for a client that will
    # eventually run unattended on a gateway device.
    async with Client(url=url) as client:
        print(f"Connected to {url}")

        # Every node in OPC-UA has a path you can navigate, similar to
        # a filesystem. get_child() walks the tree: Objects -> CNCMill1 -> Temperature
        objects = client.nodes.objects

        machine = await objects.get_child("2:CNCMill1")
        # "2:" is the namespace index we registered on the server side.
        # OPC-UA prefixes node names with their namespace index to avoid
        # collisions between different vendors' machines.

        temperature = await machine.get_child("2:Temperature")
        vibration = await machine.get_child("2:Vibration")
        rpm = await machine.get_child("2:RPM")
        error_code = await machine.get_child("2:ErrorCode")

        # Poll and print every second - a simple read loop.
        # (In Phase 2 we'll replace this print with an MQTT publish.)
        while True:
            t = await temperature.read_value()
            v = await vibration.read_value()
            r = await rpm.read_value()
            e = await error_code.read_value()

            print(f"[CLIENT READ] Temp={t}C  Vib={v}  RPM={r}  Error={e}")

            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
