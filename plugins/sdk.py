import logging

logger = logging.getLogger(__name__)

class MemoryProxy:
    def __init__(self, brain, permissions):
        self.brain = brain
        self.permissions = permissions
        
    def read(self, key: str):
        if "READ_MEMORY" not in self.permissions:
            raise PermissionError("Plugin missing READ_MEMORY permission.")
        return self.brain.memory.get_memory(key)
        
    def write(self, key: str, value: str):
        if "WRITE_MEMORY" not in self.permissions:
            raise PermissionError("Plugin missing WRITE_MEMORY permission.")
        self.brain.memory.add_memory("plugin", value)

class EventProxy:
    def __init__(self, permissions):
        self.permissions = permissions
        
    def publish(self, channel: str, message: dict):
        if "PUBLISH_EVENTS" not in self.permissions:
            raise PermissionError("Plugin missing PUBLISH_EVENTS permission.")
        from brain.event_bus import event_bus
        event_bus.publish(channel, message)

class PluginSDK:
    """
    The only object injected into the plugin's global namespace.
    Restricts capabilities based on the manifest permissions.
    """
    def __init__(self, brain, permissions: list):
        self.permissions = permissions
        self.memory = MemoryProxy(brain, permissions)
        self.events = EventProxy(permissions)
        
    def log(self, message: str):
        logger.info(f"[PLUGIN] {message}")
