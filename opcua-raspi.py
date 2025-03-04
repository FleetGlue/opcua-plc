#!/usr/bin/env python3
# OPC UA Server with Virtual and Physical Devices

from opcua import Server, ua
import time
import logging
import signal
import sys
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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


class BaseDevice:
    """Base class for all devices"""
    
    def __init__(self, name, update_interval=1):
        self.name = name
        self.update_interval = update_interval
        self.device_node = None
        self.thread = None
        self.running = False
    
    def initialize(self, server, namespace_idx):
        """Initialize the device in the OPC UA server"""
        root = server.nodes.objects
        self.device_node = root.add_object(namespace_idx, self.name)
        self._setup_nodes(server, namespace_idx)
    
    def _setup_nodes(self, server, namespace_idx):
        """Set up OPC UA nodes for this device - to be implemented by subclasses"""
        pass
    
    def start(self):
        """Start the device operation in a separate thread"""
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Device {self.name} started")
    
    def _run(self):
        """Main device logic - to be implemented by subclasses"""
        pass
    
    def stop(self):
        """Stop the device operation"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info(f"Device {self.name} stopped")


class VirtualSwitch(BaseDevice):
    """Virtual switch that toggles between ON and OFF states"""
    
    def __init__(self, name="VirtualSwitch", update_interval=2):
        super().__init__(name, update_interval)
        self.switch_node = None
        self.timestamp_node = None
    
    def _setup_nodes(self, server, namespace_idx):
        """Set up OPC UA nodes for the virtual switch"""
        # Create the switch variable
        self.switch_node = self.device_node.add_variable(namespace_idx, "State", False)
        self.switch_node.set_writable()  # Allow clients to write to it
        
        # Add metadata
        self.device_node.add_variable(namespace_idx, "Type", "Switch")
        self.device_node.add_variable(namespace_idx, "Virtual", True)
        self.timestamp_node = self.device_node.add_variable(namespace_idx, "LastToggleTime", "")
        self.timestamp_node.set_writable()
    
    def _run(self):
        """Toggle the switch state periodically"""
        state = False
        while self.running:
            # Toggle switch state
            state = not state
            self.switch_node.set_value(state)
            
            # Update timestamp
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            self.timestamp_node.set_value(current_time)
            
            logger.info(f"{self.name} state updated: {state} at {current_time}")
            
            # Wait for next toggle
            time.sleep(self.update_interval)


class PhysicalButton(BaseDevice):
    """Physical button that reads GPIO input"""
    
    def __init__(self, name="PhysicalButton", pin=None, update_interval=0.1):
        super().__init__(name, update_interval)
        self.pin = pin
        self.button_node = None
        self.press_count_node = None
        self.press_count = 0
        
        # We'll implement GPIO handling when it's needed
        self.gpio_available = False
        try:
            # This is just a placeholder - we'd import RPi.GPIO or similar here
            # import RPi.GPIO as GPIO
            # self.gpio_available = True
            pass
        except ImportError:
            logger.warning(f"GPIO library not available. {name} will simulate button presses.")
    
    def _setup_nodes(self, server, namespace_idx):
        """Set up OPC UA nodes for the physical button"""
        # Create the button state variable
        self.button_node = self.device_node.add_variable(namespace_idx, "Pressed", False)
        
        # Create a press counter
        self.press_count_node = self.device_node.add_variable(namespace_idx, "PressCount", 0)
        
        # Add metadata
        self.device_node.add_variable(namespace_idx, "Type", "Button")
        self.device_node.add_variable(namespace_idx, "Virtual", not self.gpio_available)
        self.device_node.add_variable(namespace_idx, "Pin", self.pin if self.pin is not None else "None")
    
    def _run(self):
        """Read the button state from GPIO or simulate if unavailable"""
        if self.gpio_available and self.pin is not None:
            self._run_physical()
        else:
            self._run_simulated()
    
    def _run_physical(self):
        """Read actual GPIO for button state"""
        # This would be implemented with actual GPIO code
        # For now, just placeholder
        pass
        
    def _run_simulated(self):
        """Simulate random button presses for testing"""
        import random
        last_state = False
        
        while self.running:
            # Randomly change state with low probability
            if random.random() < 0.05:  # 5% chance of state change
                new_state = not last_state
                self.button_node.set_value(new_state)
                
                # If going from not pressed to pressed, increment counter
                if new_state and not last_state:
                    self.press_count += 1
                    self.press_count_node.set_value(self.press_count)
                    logger.info(f"{self.name} pressed! Count: {self.press_count}")
                
                last_state = new_state
            
            time.sleep(self.update_interval)


class PhysicalLight(BaseDevice):
    """Physical light that controls GPIO output"""
    
    def __init__(self, name="PhysicalLight", pin=None, update_interval=0.5):
        super().__init__(name, update_interval)
        self.pin = pin
        self.light_node = None
        
        # We'll implement GPIO handling when it's needed
        self.gpio_available = False
        try:
            # This is just a placeholder - we'd import RPi.GPIO or similar here
            # import RPi.GPIO as GPIO
            # self.gpio_available = True
            pass
        except ImportError:
            logger.warning(f"GPIO library not available. {name} will simulate light state.")
    
    def _setup_nodes(self, server, namespace_idx):
        """Set up OPC UA nodes for the physical light"""
        # Create the light state variable
        self.light_node = self.device_node.add_variable(namespace_idx, "State", False)
        self.light_node.set_writable()  # Allow clients to control the light
        
        # Add metadata
        self.device_node.add_variable(namespace_idx, "Type", "Light")
        self.device_node.add_variable(namespace_idx, "Virtual", not self.gpio_available)
        self.device_node.add_variable(namespace_idx, "Pin", self.pin if self.pin is not None else "None")
    
    def _run(self):
        """Monitor the light node and update GPIO output accordingly"""
        if self.gpio_available and self.pin is not None:
            self._run_physical()
        else:
            self._run_simulated()
    
    def _run_physical(self):
        """Control actual GPIO for light state"""
        # This would be implemented with actual GPIO code
        # For now, just placeholder
        pass
        
    def _run_simulated(self):
        """Log light state changes for testing"""
        last_state = self.light_node.get_value()
        logger.info(f"{self.name} initial state: {last_state}")
        
        while self.running:
            current_state = self.light_node.get_value()
            
            # Log state changes
            if current_state != last_state:
                logger.info(f"{self.name} changed to: {current_state}")
                last_state = current_state
            
            time.sleep(self.update_interval)


def main():
    # Create the OPC UA server
    opcua_server = OPCUAServer(
        endpoint="opc.tcp://0.0.0.0:4840/freeopcua/server/",
        namespace="http://example.org/fleetglue"
    )
    
    # Add some devices
    virtual_switch = VirtualSwitch(name="VirtualSwitch", update_interval=2)
    opcua_server.add_device(virtual_switch)
    
    # Add a simulated button (no GPIO)
    button = PhysicalButton(name="Button1", pin=17)
    opcua_server.add_device(button)
    
    # Add a simulated light (no GPIO)
    light = PhysicalLight(name="Light1", pin=18)
    opcua_server.add_device(light)
    
    try:
        # Start the server and all devices
        opcua_server.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        opcua_server.stop()

if __name__ == "__main__":
    main()
