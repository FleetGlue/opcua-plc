import time

from .base import BaseDevice, logger, COUNT_NODE, STATE_NODE, TIME_NODE, TYPE_NODE, VIRTUALIZED_NODE


class VirtualButton(BaseDevice):
    def __init__(self, name="VirtualButton", pin=None, update_interval=0.1):
        super().__init__(name, update_interval)
        self.pin = pin
        self.button_node = None
        self.press_count_node = None
        self.press_count = 0

    def _setup_nodes(self, namespace_idx):
        self.button_node = self.device_node.add_variable(namespace_idx, STATE_NODE, False)
        self.button_node.set_writable()

        self.timestamp_node = self.device_node.add_variable(namespace_idx, TIME_NODE, "")
        self.timestamp_node.set_writable()

        self.press_count_node = self.device_node.add_variable(namespace_idx, COUNT_NODE, 0)
        self.press_count_node.set_writable()

        # metadata
        self.device_node.add_variable(namespace_idx, TYPE_NODE, "Button")
        self.device_node.add_variable(namespace_idx, VIRTUALIZED_NODE, True)

    def press(self):
        self.button_node.set_value(True)
        self.timestamp_node.set_value(time.time())
        self.press_count += 1
        self.press_count_node.set_value(self.press_count)
        logger.info(f"{self.name} pressed! Count: {self.press_count}")

    def release(self):
        self.button_node.set_value(False)
        self.timestamp_node.set_value(time.time())
        logger.info(f"{self.name} released!")

    def press_and_release(self):
        self.button_node.set_value(True)
        self.timestamp_node.set_value(time.time())
        self.press_count += 1
        self.press_count_node.set_value(self.press_count)
        logger.info(f"{self.name} pressed! Count: {self.press_count}")
        self.button_node.set_value(False)
        self.timestamp_node.set_value(time.time())

    def get_press_count(self):
        return self.press_count

    def get_last_change_timestamp(self):
        return self.timestamp_node.get_value()
