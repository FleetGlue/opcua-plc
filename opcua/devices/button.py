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


class VirtualButton(BaseDevice):
    def __init__(self, name="VirtualButton", pin=None, update_interval=0.1):
        super().__init__(name, update_interval)
        self.pin = pin
        self.button_node = None
        self.press_count_node = None
        self.press_count = 0

    def _setup_nodes(self, namespace_idx):
        self.button_node = self.device_node.add_variable(namespace_idx, STATE_REGISTER, False)
        self.button_node.set_writable()

        self.timestamp_node = self.device_node.add_variable(namespace_idx, TIME_REGISTER, "")
        self.timestamp_node.set_writable()

        self.press_count_node = self.device_node.add_variable(namespace_idx, COUNT_REGISTER, 0)
        self.press_count_node.set_writable()

        # metadata
        self.device_node.add_variable(namespace_idx, TYPE_REGISTER, "Button")
        self.device_node.add_variable(namespace_idx, VIRTUALIZED_REGISTER, True)

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
