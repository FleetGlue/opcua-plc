import logging
import threading

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logging.getLogger("opcua").setLevel(logging.WARNING)

COUNT_REGISTER = "Count"
STATE_REGISTER = "State"
TYPE_REGISTER = "Type"
VIRTUALIZED_REGISTER = "Virtual"
TIME_REGISTER = "LastStateChange"


class BaseDevice:
    def __init__(self, name, update_interval=1):
        self.name = name
        self.update_interval = update_interval
        self.device_node = None
        self.thread = None
        self.running = False

    def initialize(self, server, namespace_idx):
        root = server.nodes.objects
        self.device_node = root.add_object(namespace_idx, self.name)
        self._setup_nodes(namespace_idx)

    def _setup_nodes(self, namespace_idx):
        """Set up nodes for this device - overwrite this"""
        pass

    def start(self):
        """Called by OPCUAServer"""
        self.running = True
        if hasattr(self, "_run"):
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
        logger.info(f"Device {self.name} started")

    def _run(self):
        """Main device logic - overwrite this"""
        pass

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info(f"Device {self.name} stopped")
