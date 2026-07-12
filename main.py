import sys
import os
import traceback

def log_startup_error(exc_type, exc_value, exc_tb):
    # Print the exception traceback to stderr immediately
    traceback.print_exception(exc_type, exc_value, exc_tb, file=sys.stderr)
    
    # Write details to startup_error.log
    try:
        tb_list = traceback.extract_tb(exc_tb)
        failing_file = "Unknown"
        failing_line = -1
        if tb_list:
            failing_file = tb_list[-1].filename
            failing_line = tb_list[-1].lineno
            
        log_content = []
        log_content.append("=== STARTUP ERROR LOG ===")
        log_content.append(f"Exception Type: {exc_type.__name__ if exc_type else 'Unknown'}")
        log_content.append(f"Exception Value: {exc_value}")
        log_content.append(f"Failing File: {failing_file}")
        log_content.append(f"Failing Line Number: {failing_line}")
        log_content.append(f"Current Working Directory (cwd): {os.getcwd()}")
        log_content.append(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'Not Frozen')}")
        log_content.append(f"sys.executable: {sys.executable}")
        log_content.append(f"os.getcwd(): {os.getcwd()}")
        log_content.append("\n--- FULL TRACEBACK ---")
        log_content.append("".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        log_content.append("=========================")
        
        with open("startup_error.log", "w", encoding="utf-8") as f:
            f.write("\n".join(log_content))
    except Exception as write_err:
        print(f"Failed to write startup_error.log: {write_err}", file=sys.stderr)

try:
    # ── Instrumentation must be imported FIRST (monkey-patches file I/O calls) ──
    import utils.instrumentation

    import logging
    import time

    # ── Provision all writable directories before anything else touches the FS ──
    from utils.resource_manager import RM
    RM.provision()

    try:
        from utils.recovery import CrashRecoverySystem
        recovery = CrashRecoverySystem()
        recovery.run_health_check_and_repair()
    except Exception as e:
        print(f"Startup crash recovery check failed: {e}", file=sys.stderr)

    logger = logging.getLogger(__name__)

    _STARTUP_T0 = time.monotonic()

    DEBUG_MODE = "--debug" in sys.argv or os.environ.get("DEBUG_STARTUP") == "True"

    def global_excepthook(exc_type, exc_value, exc_traceback):
        """Global unhandled exception handler — captures and displays fatal errors."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Write to writable startup.log
        startup_log = RM.logs() / "startup.log"
        try:
            startup_log.parent.mkdir(parents=True, exist_ok=True)
            with open(str(startup_log), "a", encoding="utf-8") as f:
                f.write("\n==================================================\n")
                f.write(f"UNHANDLED EXCEPTION: {exc_type.__name__}: {exc_value}\n")
                traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
                f.write("==================================================\n")
        except Exception:
            pass

        # Log using python logger
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

        # Show QMessageBox
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            from version import APP_NAME
            app = QApplication.instance() or QApplication(sys.argv)
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle(f"{APP_NAME} - Fatal Startup Error")
            msg_box.setText(f"A critical error occurred:\n{exc_value}")
            msg_box.setDetailedText("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
            msg_box.exec()
        except Exception as ui_exc:
            logger.error(f"Failed to show error dialog: {ui_exc}")

    sys.excepthook = global_excepthook

    def main() -> None:
        """Launch the Khushi AI PySide6 Desktop Application."""
        try:
            from ui.app import launch_gui
            exit_code = launch_gui(debug=DEBUG_MODE)
        except Exception as exc:
            logger.critical("Fatal error launching desktop interface: %s", exc, exc_info=True)
            print(f"Fatal error: {exc}", file=sys.stderr)
            exit_code = 1
        finally:
            # Write startup diagnostics on every launch
            try:
                duration = time.monotonic() - _STARTUP_T0
                RM.write_startup_log(duration)
                RM.write_startup_report_json(duration)
            except Exception:
                pass

        sys.exit(exit_code)

except Exception:
    exc_type, exc_value, exc_tb = sys.exc_info()
    log_startup_error(exc_type, exc_value, exc_tb)
    sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        exc_type, exc_value, exc_tb = sys.exc_info()
        log_startup_error(exc_type, exc_value, exc_tb)
        sys.exit(1)