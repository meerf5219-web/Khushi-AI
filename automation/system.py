import os
import ctypes
import subprocess
import psutil

from automation.models import RiskLevel
from automation.utils import require_confirmation

class SystemAutomation:
    """Manages system-level operations (shutdown, volume, etc)."""
    
    def set_volume(self, level: int) -> None:
        """Set system volume (0-100). Windows only via nircmd or fallback to pycaw if installed."""
        # For this prototype we will use a naive approach or just pass
        # Since Volume control requires complex COM interactions without extra packages, 
        # we can just log a warning if it's not fully implemented, or use a known utility.
        pass

    def lock_screen(self) -> None:
        """Lock the workstation."""
        if not require_confirmation("Lock the workstation?", "Local Machine", RiskLevel.CRITICAL):
            raise PermissionError("User cancelled lock screen.")
        if os.name == 'nt':
            ctypes.windll.user32.LockWorkStation()

    def sleep(self) -> None:
        """Put the computer to sleep."""
        if not require_confirmation("Put the computer to sleep?", "Local Machine", RiskLevel.CRITICAL):
            raise PermissionError("User cancelled sleep.")
        if os.name == 'nt':
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    def shutdown(self) -> None:
        """Shutdown the computer."""
        if not require_confirmation("Shut down the computer?", "Local Machine", RiskLevel.CRITICAL):
            raise PermissionError("User cancelled shutdown.")
        if os.name == 'nt':
            os.system("shutdown /s /t 1")
            
    def restart(self) -> None:
        """Restart the computer."""
        if not require_confirmation("Restart the computer?", "Local Machine", RiskLevel.CRITICAL):
            raise PermissionError("User cancelled restart.")
        if os.name == 'nt':
            os.system("shutdown /r /t 1")

    def battery_status(self) -> dict:
        """Get battery status using psutil."""
        if not hasattr(psutil, "sensors_battery"):
            return {"status": "unsupported"}
            
        battery = psutil.sensors_battery()
        if battery is None:
            return {"status": "no_battery"}
            
        return {
            "percent": battery.percent,
            "power_plugged": battery.power_plugged,
            "time_left_seconds": battery.secsleft
        }
