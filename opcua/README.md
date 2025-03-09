# OPC UA Tools

Simple OPC UA server and client implementation for virtual devices.

## Installation

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate 

# Install requirements
pip install -r requirements.txt

# Start the OPC UA server with virtual devices (must be started first)
python opcua.server

# Start the interactive client to connect to your server
python opcua.client
```

## LAN Access

To access the OPC UA server from other devices on the same network:

1. Find the IP address of the machine running the server

2. The server is configured by default to bind to address 0.0.0.0 (all network interfaces) on port 4840, which makes it accessible from other devices on the network

3. On other devices, connect to the server using the server machine's IP address
    ```bash
    endpoint="opc.tcp://{server_ip}:4840/freeopcua/server/",
    namespace="http://example.org/fleetglue"
    ```