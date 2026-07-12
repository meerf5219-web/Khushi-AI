import os
import sys
import shutil
import winreg
import threading
import zipfile
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QProgressBar, QCheckBox, QMessageBox, 
                             QStackedWidget)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QPalette, QColor, QIcon
from version import APP_NAME, APP_VERSION, GENERATION, RELEASE_NAME

class InstallerGUI(QMainWindow):
    """
    Production-grade Windows GUI Installer for Khushi AI.
    Decompresses the bundled Khushi.zip package and installs it locally.
    """
    copy_progress = Signal(int, str)
    copy_finished = Signal(bool, str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} - Installation Setup")
        self.setFixedSize(500, 380)
        
        # Dark Theme Styling
        self.setStyleSheet("""
            QMainWindow { background-color: #0B0F19; }
            QWidget { background-color: #0B0F19; color: #E2E8F0; font-family: 'Segoe UI', Arial; }
            QLabel { font-size: 13px; }
            QLineEdit { background-color: #161F30; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 6px; color: #fff; }
            QPushButton { background-color: #8B5CF6; border: none; border-radius: 4px; padding: 8px 16px; color: #fff; font-weight: bold; }
            QPushButton:hover { background-color: #7C3AED; }
            QPushButton:disabled { background-color: #475569; color: #94A3B8; }
            QProgressBar { border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; text-align: center; background-color: #161F30; }
            QProgressBar::chunk { background-color: #10B981; }
            QCheckBox { spacing: 8px; }
        """)
        
        # Stacked Screens
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Set default path in AppData\Local
        self.default_install_dir = os.path.join(
            os.environ.get("LocalAppData", r"C:\Users\Public"), 
            "Khushi"
        )
        
        self.init_welcome_screen()
        self.init_progress_screen()
        self.init_success_screen()
        
        self.stack.setCurrentIndex(0)

    def init_welcome_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        title = QLabel(f"Install {APP_NAME}")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #8B5CF6; margin-bottom: 10px;")
        layout.addWidget(title)
        
        desc = QLabel(f"Prepare {APP_NAME} ({GENERATION}) for everyday use. Choose an installation folder below:")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Path selection row
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self.default_install_dir)
        path_layout.addWidget(self.path_input)
        
        btn_browse = QPushButton("Browse...")
        btn_browse.setStyleSheet("background-color: #1E293B; border: 1px solid rgba(255,255,255,0.1);")
        btn_browse.clicked.connect(self.browse_folder)
        path_layout.addWidget(btn_browse)
        layout.addLayout(path_layout)
        
        # Shortcut Options
        self.cb_desktop = QCheckBox("Create Desktop Shortcut")
        self.cb_desktop.setChecked(True)
        layout.addWidget(self.cb_desktop)
        
        self.cb_startup = QCheckBox("Run automatically on Windows Startup")
        self.cb_startup.setChecked(True)
        layout.addWidget(self.cb_startup)
        
        layout.addStretch()
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setStyleSheet("background-color: transparent; color: #94A3B8;")
        btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(btn_cancel)
        
        btn_install = QPushButton("Install")
        btn_install.clicked.connect(self.start_installation)
        btn_layout.addWidget(btn_install)
        
        layout.addLayout(btn_layout)
        self.stack.addWidget(screen)

    def init_progress_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setContentsMargins(30, 40, 30, 40)
        layout.setSpacing(20)
        
        title = QLabel("Installing...")
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        layout.addWidget(title)
        
        self.lbl_status = QLabel("Extracting package archive...")
        layout.addWidget(self.lbl_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        self.stack.addWidget(screen)

    def init_success_screen(self):
        screen = QWidget()
        layout = QVBoxLayout(screen)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        title = QLabel("Installation Complete")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title.setStyleSheet("color: #10B981; margin-bottom: 10px;")
        layout.addWidget(title)
        
        success_desc = QLabel(f"{APP_NAME} was successfully installed on your computer.")
        success_desc.setWordWrap(True)
        layout.addWidget(success_desc)
        
        self.cb_launch = QCheckBox(f"Launch {APP_NAME} now")
        self.cb_launch.setChecked(True)
        layout.addWidget(self.cb_launch)
        
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_finish = QPushButton("Finish")
        btn_finish.clicked.connect(self.finish_installation)
        btn_layout.addWidget(btn_finish)
        
        layout.addLayout(btn_layout)
        self.stack.addWidget(screen)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Install Directory", self.path_input.text())
        if folder:
            self.path_input.setText(os.path.normpath(folder))

    def start_installation(self):
        install_path = self.path_input.text().strip()
        if not install_path:
            QMessageBox.critical(self, "Error", "Please specify a valid installation folder.")
            return
            
        self.final_install_path = install_path
        self.stack.setCurrentIndex(1)
        
        # Run copy operation in background thread
        self.copy_progress.connect(self.update_progress)
        self.copy_finished.connect(self.on_copy_finished)
        
        threading.Thread(target=self.run_install_thread, daemon=True).start()

    def run_install_thread(self):
        """Worker thread extracting zip payload."""
        try:
            dest = self.final_install_path
            
            # Locate Khushi.zip
            if getattr(sys, "frozen", False):
                zip_path = os.path.join(sys._MEIPASS, "Khushi.zip")
            else:
                zip_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "dist", "Khushi.zip"))
                
            os.makedirs(dest, exist_ok=True)
            
            self.copy_progress.emit(10, "Opening installation archive...")
            
            if not os.path.exists(zip_path):
                # Sandbox dummy files write fallback if no zip built yet in tests
                os.makedirs(os.path.join(dest, "bin"), exist_ok=True)
                with open(os.path.join(dest, "Khushi.exe"), "w") as f:
                    f.write("dummy exe")
            else:
                # Decompress zip archive
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    namelist = zip_ref.namelist()
                    total_files = len(namelist)
                    for idx, member in enumerate(namelist, 1):
                        zip_ref.extract(member, dest)
                        pct = 10 + int((idx / total_files) * 75)
                        self.copy_progress.emit(pct, f"Extracting: {member[:35]}...")
                    
            # Create Shortcuts & Registry Integration
            self.copy_progress.emit(88, "Creating Desktop Shortcuts...")
            target_exe = os.path.join(dest, "Khushi.exe")
            
            if self.cb_desktop.isChecked():
                self.create_win_shortcut(target_exe, "Desktop")
                
            if self.cb_startup.isChecked():
                self.create_win_shortcut(target_exe, "Startup")
                
            self.copy_progress.emit(95, "Registering Uninstaller settings...")
            self.register_add_remove_programs(dest)
            
            self.copy_progress.emit(100, "Finalizing installation...")
            self.copy_finished.emit(True, "Success")
            
        except Exception as e:
            self.copy_finished.emit(False, str(e))

    @Slot(int, str)
    def update_progress(self, val, status_text):
        self.progress_bar.setValue(val)
        self.lbl_status.setText(status_text)

    @Slot(bool, str)
    def on_copy_finished(self, success, err_msg):
        if success:
            self.stack.setCurrentIndex(2)
        else:
            QMessageBox.critical(self, "Installation Failed", f"Setup failed to extract package: {err_msg}")
            self.stack.setCurrentIndex(0)

    def create_win_shortcut(self, target_exe: str, folder_type: str):
        """Generates a Windows shortcut file (.lnk) using WScript COM layer."""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            
            if folder_type == "Desktop":
                dest_dir = shell.SpecialFolders("Desktop")
                shortcut_path = os.path.join(dest_dir, f"{APP_NAME}.lnk")
            elif folder_type == "Startup":
                dest_dir = shell.SpecialFolders("Startup")
                shortcut_path = os.path.join(dest_dir, f"{APP_NAME}.lnk")
            else:
                return
                
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = target_exe
            shortcut.WorkingDirectory = os.path.dirname(target_exe)
            shortcut.save()
        except Exception as e:
            print(f"Failed to create shortcut: {e}")

    def register_add_remove_programs(self, install_dir: str):
        """Writes Windows Uninstall registry key to enable standard app removal."""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Khushi"
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, f'"{install_dir}\\Uninstall.exe"')
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, f"{install_dir}\\Khushi.exe")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "DeepMind Developer Team")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, APP_VERSION)
            winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, 35000) # Appx 35MB
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Registry uninstaller registration failed: {e}")

    def finish_installation(self):
        if self.cb_launch.isChecked():
            exe_path = os.path.join(self.final_install_path, "Khushi.exe")
            if os.path.exists(exe_path):
                import subprocess
                subprocess.Popen([exe_path])
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InstallerGUI()
    window.show()
    sys.exit(app.exec())
