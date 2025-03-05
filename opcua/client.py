#!/usr/bin/env python3

import logging
import time
from opcua import Client

from devices.base import COUNT_REGISTER, STATE_REGISTER, TIME_REGISTER

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("opcua").setLevel(logging.WARNING)


class OPCUAClient:
    def __init__(
        self,
        endpoint="opc.tcp://localhost:4840/freeopcua/server/",
        namespace="http://example.org/fleetglue",
    ):
        self.endpoint = endpoint
        self.namespace = namespace
        self.client = None

    def connect(self):
        logger.debug(f"Connecting to OPC UA server at {self.endpoint}")
        self.client = Client(self.endpoint)
        self.client.connect()
        self.namespace_idx = self.client.get_namespace_index(self.namespace)
        logger.info(f"Connected to OPC UA server at {self.endpoint}")
        logger.info(f"Namespace '{self.namespace}' has index: {self.namespace_idx}")

    def disconnect(self):
        if self.client:
            self.client.disconnect()
            logger.info("Disconnected from OPC UA server")

    def get_devices(self):
        """List all devices on the server"""
        try:
            objects = self.client.get_objects_node()
            children = objects.get_children()

            logger.info("\nAvailable Devices:")
            for child in children:
                name = child.get_browse_name().Name
                logger.info(f"- {name}")

            return children
        except Exception as e:
            logger.error(f"Error listing devices: {e}")
            return []

    def get_device(self, device_name):
        try:
            objects = self.client.get_objects_node()
            device = objects.get_child(f"{self.namespace_idx}:{device_name}")
            return device
        except Exception as e:
            logger.error(f"Error getting device: {e}")
            return None

    def get_device_info(self, device_name):
        try:
            device = self.get_device(device_name)
            variables = device.get_variables()

            logger.info(f"\nDevice: {device_name}")
            logger.info("Properties:")
            for var in variables:
                name = (var.get_browse_name()).Name
                value = var.get_value()
                logger.info(f"  {name}: {value}")

            return variables
        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return []

    def get_node(self, device_name, node_name):
        device = self.get_device(device_name)
        return device.get_child(f"{self.namespace_idx}:{node_name}")

    def get_node_value(self, device_name, node_name):
        node = self.get_node(device_name, node_name)
        return node.get_value()

    def press_button(self, device_name):
        try:
            state_node = self.get_node(device_name, STATE_REGISTER)
            state_node.set_value(True)

            time_node = self.get_node(device_name, TIME_REGISTER)
            time_node.set_value(str(time.time()))

            count_node = self.get_node(device_name, COUNT_REGISTER)
            current_count = count_node.get_value()
            count_node.set_value(current_count + 1)

            logger.info(f"Button {device_name} pressed! Count: {current_count + 1}")
        except Exception as e:
            logger.error(f"Error pressing button: {e}")

    def release_button(self, device_name):
        try:
            state_node = self.get_node(device_name, STATE_REGISTER)
            state_node.set_value(False)

            time_node = self.get_node(device_name, TIME_REGISTER)
            time_node.set_value(str(time.time()))

            logger.info(f"Button {device_name} released!")
        except Exception as e:
            logger.error(f"Error releasing button: {e}")

    def press_and_release_button(self, device_name):
        try:
            self.press_button(device_name)
            self.release_button(device_name)
        except Exception as e:
            logger.error(f"Error in press and release sequence: {e}")

    def toggle_switch(self, device_name):
        try:
            state_node = self.get_node(device_name, STATE_REGISTER)
            current_state = state_node.get_value()
            logger.info(f"Switch {device_name} current state: {current_state}")

            new_state = not current_state
            state_node.set_value(new_state)

            time_node = self.get_node(device_name, TIME_REGISTER)
            time_node.set_value(str(time.time()))

            count_node = self.get_node(device_name, COUNT_REGISTER)
            current_count = count_node.get_value()
            count_node.set_value(current_count + 1)

            logger.info(f"Switch {device_name} state set to: {new_state}")
            return new_state
        except Exception as e:
            logger.error(f"Error toggling switch: {e}")
            return None

    def get_count_node(self, device_name):
        try:
            count = self.get_node_value(device_name, COUNT_REGISTER)
            return count
        except Exception as e:
            logger.error(f"Error getting button press count: {e}")
            return None

    def get_last_change_timestamp(self, device_name):
        try:
            timestamp = self.get_node_value(device_name, TIME_REGISTER)
            return timestamp
        except Exception as e:
            logger.error(f"Error getting switch timestamp: {e}")
            return None


def interactive_menu(client):
    """Display an interactive menu for the client"""
    try:
        client.connect()

        while True:
            print("\n--- OPC UA Client Menu ---")
            print("1. List all devices")
            print("2. Get device information")
            print("3. Toggle a switch")
            print("4. Press and Release Button")
            print("5. Press Button")
            print("6. Release Button")
            print("7. Get device count")
            print("8. Get most recent device press time")
            print("0. Exit")

            choice = input("Enter choice (0-7): ")

            if choice == "0":
                print("Exiting...")
                break
            elif choice == "1":
                client.get_devices()
            elif choice == "2":
                device_name = (
                    input("Enter device name: (default: VirtualSwitch): ") or "VirtualSwitch"
                )
                client.get_device_info(device_name)
            elif choice == "3":
                device_name = (
                    input("Enter switch device name (default: VirtualSwitch): ") or "VirtualSwitch"
                )
                client.toggle_switch(device_name)
            elif choice == "4":
                device_name = input("Enter button device name (default: Button1): ") or "Button1"
                client.press_and_release_button(device_name)
            elif choice == "5":
                device_name = input("Enter button device name (default: Button1): ") or "Button1"
                client.press_button(device_name)
            elif choice == "6":
                device_name = input("Enter button device name (default: Button1): ") or "Button1"
                client.release_button(device_name)
            elif choice == "7":
                device_name = input("Enter button device name (default: Button1): ") or "Button1"
                count = client.get_count_node(device_name)
                print(f"Button press count: {count}")
            elif choice == "8":
                device_name = input("Enter button device name (default: Button1): ") or "Button1"
                timestamp = client.get_last_change_timestamp(device_name)
                print(f"Last button press was at timestamp: {timestamp}")
            else:
                print("Invalid choice. Please try again.")

    except Exception as e:
        logger.error(f"Error in interactive menu: {e}")
    finally:
        client.disconnect()


def main():
    logger.info("Starting OPC UA client")
    endpoint = "opc.tcp://localhost:4840/freeopcua/server/"
    namespace = "http://example.org/fleetglue"
    client = OPCUAClient(endpoint, namespace)
    try:
        interactive_menu(client)
    except KeyboardInterrupt:
        logger.info("Client interrupted by user")
    except Exception as e:
        logger.error(f"Error running client: {e}")

    logger.info("OPC UA client closed")


if __name__ == "__main__":
    main()
