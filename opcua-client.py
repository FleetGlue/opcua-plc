#!/usr/bin/env python3
# OPC UA Client for basic device interactions

import sys
import time
import logging
import asyncio
from opcua import Client

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OPCUAClient:
    """Simple OPC UA client for interacting with devices"""
    
    def __init__(self, endpoint="opc.tcp://localhost:4840/freeopcua/server/"):
        self.endpoint = endpoint
        self.client = None
        
    async def connect(self):
        """Connect to the OPC UA server"""
        self.client = Client(self.endpoint)
        await self.client.connect_async()
        logger.info(f"Connected to OPC UA server at {self.endpoint}")
        
    async def disconnect(self):
        """Disconnect from the OPC UA server"""
        if self.client:
            await self.client.disconnect_async()
            logger.info("Disconnected from OPC UA server")
    
    async def list_devices(self):
        """List all devices on the server"""
        try:
            objects = self.client.get_objects_node()
            children = await objects.get_children()
            
            logger.info("\nAvailable Devices:")
            for child in children:
                name = (await child.read_browse_name()).Name
                logger.info(f"- {name}")
                
            return children
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return []
    
    async def get_device_info(self, device_name):
        """Get information about a specific device"""
        try:
            objects = self.client.get_objects_node()
            device = await objects.get_child([device_name])
            
            # Get all variables
            variables = await device.get_variables()
            
            logger.info(f"\nDevice: {device_name}")
            logger.info("Properties:")
            
            for var in variables:
                name = (await var.read_browse_name()).Name
                value = await var.read_value()
                logger.info(f"  {name}: {value}")
                
            return variables
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return []
    
    async def toggle_switch(self, device_name="VirtualSwitch"):
        """Toggle a switch device"""
        try:
            objects = self.client.get_objects_node()
            device = await objects.get_child([device_name])
            state_node = await device.get_child(["State"])
            
            # Read current state
            current_state = await state_node.get_value()
            logger.info(f"{device_name} current state: {current_state}")
            
            # Toggle state
            new_state = not current_state
            await state_node.set_value(new_state)
            logger.info(f"{device_name} state set to: {new_state}")
            
            return new_state
        except Exception as e:
            logger.error(f"Error toggling switch: {e}")
            return None
    
    async def control_light(self, state, device_name="Light1"):
        """Turn a light on or off"""
        try:
            objects = self.client.get_objects_node()
            device = await objects.get_child([device_name])
            state_node = await device.get_child(["State"])
            
            # Set new state
            await state_node.set_value(state)
            logger.info(f"{device_name} state set to: {state}")
            
            return True
        except Exception as e:
            logger.error(f"Error controlling light: {e}")
            return False
    
    async def get_button_count(self, device_name="Button1"):
        """Get the current press count of a button"""
        try:
            objects = self.client.get_objects_node()
            device = await objects.get_child([device_name])
            count_node = await device.get_child(["PressCount"])
            
            count = await count_node.get_value()
            logger.info(f"{device_name} press count: {count}")
            
            return count
        except Exception as e:
            logger.error(f"Error getting button count: {e}")
            return None
    
    async def monitor_button(self, duration=10, device_name="Button1"):
        """Monitor a button for presses over a duration in seconds"""
        try:
            objects = self.client.get_objects_node()
            device = await objects.get_child([device_name])
            pressed_node = await device.get_child(["Pressed"])
            count_node = await device.get_child(["PressCount"])
            
            # Get initial values
            initial_count = await count_node.get_value()
            logger.info(f"Monitoring {device_name} for {duration} seconds...")
            logger.info(f"Initial press count: {initial_count}")
            
            # Monitor for the specified duration
            start_time = time.time()
            while time.time() - start_time < duration:
                is_pressed = await pressed_node.get_value()
                current_count = await count_node.get_value()
                
                if current_count > initial_count:
                    logger.info(f"Button pressed! New count: {current_count}")
                    initial_count = current_count
                
                await asyncio.sleep(0.1)
            
            final_count = await count_node.get_value()
            logger.info(f"Monitoring complete. Final press count: {final_count}")
            
            return final_count
        except Exception as e:
            logger.error(f"Error monitoring button: {e}")
            return None

async def interactive_menu():
    """Display an interactive menu for the client"""
    client = OPCUAClient()
    
    try:
        await client.connect()
        
        while True:
            print("\n--- OPC UA Client Menu ---")
            print("1. List all devices")
            print("2. Get device information")
            print("3. Toggle a switch")
            print("4. Turn light ON")
            print("5. Turn light OFF")
            print("6. Get button press count")
            print("7. Monitor button for presses")
            print("0. Exit")
            
            choice = input("Enter choice (0-7): ")
            
            if choice == '0':
                print("Exiting...")
                break
            elif choice == '1':
                await client.list_devices()
            elif choice == '2':
                device_name = input("Enter device name: ")
                await client.get_device_info(device_name)
            elif choice == '3':
                device_name = input("Enter switch device name (default: VirtualSwitch): ") or "VirtualSwitch"
                await client.toggle_switch(device_name)
            elif choice == '4':
                device_name = input("Enter light device name (default: Light1): ") or "Light1"
                await client.control_light(True, device_name)
            elif choice == '5':
                device_name = input("Enter light device name (default: Light1): ") or "Light1"
                await client.control_light(False, device_name)
            elif choice == '6':
                device_name = input("Enter button device name (default: Button1): ") or "Button1"
                await client.get_button_count(device_name)
            elif choice == '7':
                device_name = input("Enter button device name (default: Button1): ") or "Button1"
                duration = int(input("Enter monitoring duration in seconds (default: 10): ") or "10")
                await client.monitor_button(duration, device_name)
            else:
                print("Invalid choice. Please try again.")
                
    except Exception as e:
        logger.error(f"Error in interactive menu: {e}")
    finally:
        await client.disconnect()

def main():
    """Main entry point"""
    logger.info("Starting OPC UA client")
    
    # Check if server endpoint is provided as argument
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "opc.tcp://localhost:4840/freeopcua/server/"
    
    try:
        asyncio.run(interactive_menu())
    except KeyboardInterrupt:
        logger.info("Client interrupted by user")
    except Exception as e:
        logger.error(f"Error running client: {e}")
        
    logger.info("OPC UA client closed")

if __name__ == "__main__":
    main()