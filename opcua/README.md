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