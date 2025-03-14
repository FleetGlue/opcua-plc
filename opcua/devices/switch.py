import time

from .base import (
    BaseDevice,
    logger,
    COUNT_REGISTER,
    STATE_REGISTER,
    TIME_REGISTER,
    TYPE_REGISTER,
    VIRTUALIZED_REGISTER,
)


class VirtualSwitch(BaseDevice):
    def __init__(self, name="VirtualSwitch", update_interval=2):
        super().__init__(name, update_interval)
        self.switch_node = None
        self.timestamp_node = None
        self.switch_count_node = None
        self.switch_count = 0

    def _setup_nodes(self, namespace_idx):
        """Set up OPC UA nodes (aka registers in PLC lingo) for the virtual switch"""
        self.switch_node = self.device_node.add_variable(namespace_idx, STATE_REGISTER, False)
        self.switch_node.set_writable()

        self.timestamp_node = self.device_node.add_variable(namespace_idx, TIME_REGISTER, "")
        self.timestamp_node.set_writable()

        self.switch_count_node = self.device_node.add_variable(namespace_idx, COUNT_REGISTER, 0)
        self.switch_count_node.set_writable()

        # metadata
        self.device_node.add_variable(namespace_idx, TYPE_REGISTER, "Switch")
        self.device_node.add_variable(namespace_idx, VIRTUALIZED_REGISTER, True)

    def toggle(self):
        """Toggle a switch device"""
        try:
            current_state = self.switch_node.get_value()
            logger.info(f"{self.name} current state: {current_state}")

            new_state = not current_state
            self.switch_node.set_value(new_state)
            self.timestamp_node.set_value(time.time())
            self.switch_count += 1
            self.switch_count_node.set_value(self.switch_count)
            logger.info(f"{self.name} state set to: {new_state}")
            return new_state
        except Exception as e:
            logger.error(f"Error toggling switch: {e}")
            return None

    def get_switch_count(self):
        return self.switch_count

    def get_last_change_timestamp(self):
        return self.timestamp_node.get_value()
