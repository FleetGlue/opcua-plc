#!/usr/bin/env python3

import signal
import sys
import time

from opcua import Server, ua

from devices.base import logger
from devices.button import VirtualButton
from devices.switch import VirtualSwitch


class OPCUAServer:    
    def __init__(self, endpoint="opc.tcp://0.0.0.0:4840/freeopcua/server/", 
                 namespace="http://example.org/fleetglue"):
        self.server = None
        self.endpoint = endpoint
        self.namespace = namespace
        self.namespace_idx = None
        self.devices = []
        self.running = False

    def setup(self):
        logger.debug("Configuring OPC UA server")
        self.server = Server()
        self.server.set_endpoint(self.endpoint)
        
        # Register namespace
        # Namespaces in OPC UA are used to organize different functionalities
        # e.g. Namespace X: Contains data for Production Line X
        self.namespace_idx = self.server.register_namespace(self.namespace)

        # Set up server attributes
        server_node = self.server.get_server_node()
        server_node.set_attribute(ua.AttributeIds.Description, 
                                  ua.DataValue(ua.Variant("FleetGlue OPC UA Server", ua.VariantType.String)))
        
        logger.info(f"OPCUA server configured with endpoint: {self.endpoint}")
        return self.namespace_idx
    
    def add_device(self, device):
        logger.debug(f"Adding device: {device.name}")
        if self.server is None:
            self.setup()

        self.devices.append(device)
        device.initialize(self.server, self.namespace_idx)
        logger.info(f"Added device: {device.name}")
        
    def start(self):
        logger.debug(f"Starting OPC UA Server at {self.endpoint}")
        if self.server is None:
            self.setup()

        self.server.start()
        self.running = True
        logger.info(f"OPC UA Server started at {self.endpoint}")

        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Start device threads
        for device in self.devices:
            device.start()

        try:
            while self.running:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in main thread: {e}")
            self.stop()

    def stop(self):
        if self.running:
            logger.info("Shutting down server and devices...")
            self.running = False

            for device in self.devices:
                device.stop()

            # Stop the server
            if self.server:
                self.server.stop()

            logger.info("Server stopped")

def main():
    server = OPCUAServer(
        endpoint="opc.tcp://0.0.0.0:4840/freeopcua/server/",
        namespace="http://example.org/fleetglue"
    )

    switch = VirtualSwitch(name="VirtualSwitch", update_interval=2)
    server.add_device(switch)
    
    button = VirtualButton(name="Button1", pin=17)
    server.add_device(button)
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        server.stop()

if __name__ == "__main__":
    main()