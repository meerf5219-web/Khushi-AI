import builtins
import logging
import types

logger = logging.getLogger(__name__)

# List of highly dangerous built-in functions
DANGEROUS_BUILTINS = {
    '__import__', 'eval', 'exec', 'compile', 'open', 'input', 
    'globals', 'locals', 'vars', 'dir', 'delattr', 'setattr', 'getattr'
}

class RestrictedEnvironment:
    """
    Executes plugin code in a restricted namespace.
    Provides a soft sandbox.
    """
    
    def __init__(self, permissions: list):
        self.permissions = permissions
        self._build_safe_globals()
        
    def _build_safe_globals(self):
        # Start with standard builtins
        safe_builtins = {k: v for k, v in builtins.__dict__.items() if k not in DANGEROUS_BUILTINS}
        
        # Optionally restore some builtins based on explicit permissions
        if "WRITE_FILES" in self.permissions or "READ_FILES" in self.permissions:
            safe_builtins['open'] = builtins.open
            
        # We must supply a safe __import__ proxy for allowed modules
        safe_builtins['__import__'] = self._safe_import
        
        self.sandbox_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__plugin_main__',
            '__doc__': None,
            '__package__': None,
        }
        
    def _safe_import(self, name, globals=None, locals=None, fromlist=(), level=0):
        """
        Prevents importing os, sys, subprocess, ctypes unless specifically permitted.
        """
        RESTRICTED_MODULES = {'os', 'sys', 'subprocess', 'ctypes', 'shutil', 'pty'}
        
        # Check base module name (e.g., 'os.path' -> 'os')
        base_module = name.split('.')[0]
        
        if base_module in RESTRICTED_MODULES:
            if "SYSTEM_ACCESS" not in self.permissions:
                logger.warning(f"Plugin blocked from importing dangerous module: {name}")
                raise ImportError(f"Importing '{name}' is restricted by sandbox policies.")
                
        # Passthrough to standard import
        return __import__(name, globals, locals, fromlist, level)
        
    def execute(self, code_str: str, sdk_instance) -> types.ModuleType:
        """
        Executes the raw python string in the sandbox.
        Injects the `sdk` object into globals.
        """
        self.sandbox_globals['sdk'] = sdk_instance
        
        # Create a blank module structure
        plugin_module = types.ModuleType('__plugin_main__')
        
        try:
            # Execute code directly against the sandbox dictionary
            exec(code_str, self.sandbox_globals)
            
            # Map sandbox globals into the module dictionary
            for k, v in self.sandbox_globals.items():
                setattr(plugin_module, k, v)
                
            return plugin_module
            
        except Exception as e:
            logger.error(f"Plugin execution failed in sandbox: {e}")
            raise
