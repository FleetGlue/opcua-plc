from opcua import Server, ua

class OPCUAServer:
    """Base OPC UA Server that can host multiple devices"""
    
    def __init__(self, endpoint="opc.tcp://0.0.0.0:4840/freeopcua/server/", 
                 namespace="http://example.org/devices"):
        self.server = None
        self.endpoint = endpoint
        self.namespace = namespace
        self.namespace_idx = None
        self.devices = []
        self.running = False
        
    def setup(self):
        """Initialize and configure the OPC UA server"""
        logger.info("Initializing OPC UA server...")
        self.server = Server()
        self.server.set_endpoint(self.endpoint)
        
        # Register namespace
        self.namespace_idx = self.server.register_namespace(self.namespace)
        
        # Set up server attributes
        server_node = self.server.get_server_node()
        server_node.set_attribute(ua.AttributeIds.Description, 
                                  ua.DataValue(ua.Variant("FleetGlue OPC UA Server", ua.VariantType.String)))
        
        logger.info(f"Server configured with endpoint: {self.endpoint}")
        return self.namespace_idx
    
    def add_device(self, device):
        """Add a device to the server"""
        if self.server is None:
            self.setup()
        
        self.devices.append(device)
        device.initialize(self.server, self.namespace_idx)
        logger.info(f"Added device: {device.name}")
        
    def start(self):
        """Start the OPC UA server and all device threads"""
        if self.server is None:
            self.setup()
            
        # Start the server
        self.server.start()
        self.running = True
        logger.info(f"OPC UA Server started at {self.endpoint}")
        
        # Setup signal handler for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Received shutdown signal")
            self.stop()
            sys.exit(0)
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start all device threads
        for device in self.devices:
            device.start()
        
        # Keep the main thread alive
        try:
            while self.running:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in main thread: {e}")
            self.stop()
            
    def stop(self):
        """Stop all devices and the OPC UA server"""
        if self.running:
            logger.info("Shutting down server and devices...")
            self.running = False
            
            # Stop all device threads
            for device in self.devices:
                device.stop()
                
            # Stop the server
            if self.server:
                self.server.stop()
                
            logger.info("Server stopped")
