# Phase 1 Architecture

## Overview

Two simulated machines feed data through an edge gateway into a cloud
backend, mirroring a real Industrial IoT deployment.
## Zones

- **OT / edge environment**: machines, edge gateway, MQTT broker, edge
  processing service. This is the "factory floor" side of the system.
- **IT / cloud environment**: cloud API and dashboard. This is where
  aggregated, processed data lands for storage and visualization.

The boundary between these two zones is where Phase 4 security controls
(TLS/mTLS, network segmentation) will be enforced.

## Components (status)

| Component | Protocol | Status |
|---|---|---|
| CNC Mill | OPC-UA | Done (machines/opcua_machine.py) |
| Conveyor Motor | Modbus TCP | Done (machines/modbus_machine.py) |
| Edge Gateway | reads OPC-UA + Modbus, publishes MQTT | Phase 2 |
| MQTT Broker | MQTT | Phase 2 (Mosquitto via Docker) |
| Edge Processing | consumes MQTT, detects anomalies | Phase 3 |
| Cloud API | REST | Phase 5 (FastAPI) |
| Dashboard | - | Phase 5 (Grafana + InfluxDB) |
