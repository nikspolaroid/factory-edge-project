# Factory Edge Project — Phase 1

## Setup (run these in Terminal, inside the unzipped folder)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You'll know the venv is active when your prompt shows `(venv)` at the start.

## Run the first simulated machine

```bash
python machines/opcua_machine.py
```

You should see output like:
```
Starting CNCMill1 OPC-UA server at opc.tcp://0.0.0.0:4840/freeopcua/server/
Temp=61.3C  Vib=0.287  RPM=1523  Error=0
```

Leave this running — it's your simulated machine, live and broadcasting.
Next step: build a client that connects and reads this data (same pattern
the real edge gateway will use).
