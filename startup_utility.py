#!/usr/bin/env python3
"""
Cross-platform Startup Utility for VNC QR Server
Manages auto-startup functionality for Windows and macOS
"""

import os
import sys
import platform
import subprocess
from tkinter import messagebox
import tkinter as tk

class StartupManager:
    def __init__(self):
        self.app_name = "VNCQRServer"
        self.system = platform.system()

        if self.system == "Darwin":  # macOS
            self.launch_agent_name = "com.vncqrserver.app"
            self.plist_path = os.path.expanduser(f"~/Library/LaunchAgents/{self.launch_agent_name}.plist")
        elif self.system == "Windows":
            self.registry_key = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def get_app_path(self):
        """Get the full path to the main application."""
        main_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
        if self.system == "Windows":
            return f'"{sys.executable}" "{main_py_path}"'
        else:
            return main_py_path

    def is_startup_enabled(self):
        """Check if auto-startup is currently enabled."""
        if self.system == "Darwin":
            return self._is_mac_startup_enabled()
        elif self.system == "Windows":
            return self._is_windows_startup_enabled()
        else:
            return False

    def _is_mac_startup_enabled(self):
        """Check if macOS LaunchAgent is loaded."""
        try:
            result = subprocess.run(['launchctl', 'list', self.launch_agent_name],
                                  capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False

    def _is_windows_startup_enabled(self):
        """Check if Windows registry entry exists."""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_READ) as key:
                try:
                    value, _ = winreg.QueryValueEx(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False
        except Exception:
            return False

    def enable_startup(self):
        """Enable auto-startup."""
        if self.system == "Darwin":
            return self._enable_mac_startup()
        elif self.system == "Windows":
            return self._enable_windows_startup()
        else:
            print(f"Auto-startup not supported on {self.system}")
            return False

    def _enable_mac_startup(self):
        """Enable macOS startup via LaunchAgent."""
        try:
            main_py_path = self.get_app_path()
            working_dir = os.path.dirname(main_py_path)

            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.launch_agent_name}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{main_py_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
    <key>StandardOutPath</key>
    <string>/tmp/vncqrserver.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/vncqrserver.error.log</string>
</dict>
</plist>"""

            # Ensure LaunchAgents directory exists
            os.makedirs(os.path.dirname(self.plist_path), exist_ok=True)

            # Write plist file
            with open(self.plist_path, 'w') as f:
                f.write(plist_content)

            # Load the LaunchAgent
            subprocess.run(['launchctl', 'load', self.plist_path], check=True)
            return True

        except Exception as e:
            print(f"Error enabling Mac startup: {e}")
            return False

    def _enable_windows_startup(self):
        """Enable Windows startup via registry."""
        try:
            import winreg
            app_path = self.get_app_path()
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, app_path)
            return True
        except Exception as e:
            print(f"Error enabling Windows startup: {e}")
            return False

    def disable_startup(self):
        """Disable auto-startup."""
        if self.system == "Darwin":
            return self._disable_mac_startup()
        elif self.system == "Windows":
            return self._disable_windows_startup()
        else:
            return False

    def _disable_mac_startup(self):
        """Disable macOS startup."""
        try:
            if os.path.exists(self.plist_path):
                # Unload the LaunchAgent
                subprocess.run(['launchctl', 'unload', self.plist_path],
                             capture_output=True, text=True)
                # Remove plist file
                os.remove(self.plist_path)
            return True
        except Exception as e:
            print(f"Error disabling Mac startup: {e}")
            return False

    def _disable_windows_startup(self):
        """Disable Windows startup."""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, self.app_name)
            return True
        except FileNotFoundError:
            return True  # Already not in startup
        except Exception as e:
            print(f"Error disabling Windows startup: {e}")
            return False

class StartupGUI:
    def __init__(self):
        self.startup_manager = StartupManager()
        self.root = tk.Tk()
        self.root.title("VNC QR Server - Startup Configuration")
        self.root.geometry("450x300")
        self.root.resizable(False, False)

        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")

        self.create_widgets()

    def create_widgets(self):
        """Create GUI widgets."""
        # Title
        title_label = tk.Label(self.root, text="VNC QR Server\nStartup Configuration",
                              font=("Arial", 16, "bold"), fg="#2c3e50")
        title_label.pack(pady=20)

        # System info
        system_info = tk.Label(self.root,
                             text=f"Operating System: {platform.system()} {platform.release()}",
                             font=("Arial", 10), fg="#7f8c8d")
        system_info.pack(pady=5)

        # Status frame
        status_frame = tk.Frame(self.root, bg="#ecf0f1", relief="raised", bd=2)
        status_frame.pack(fill="x", padx=20, pady=10)

        current_status = self.startup_manager.is_startup_enabled()
        status_text = "ENABLED" if current_status else "DISABLED"
        status_color = "#27ae60" if current_status else "#e74c3c"

        tk.Label(status_frame, text="Auto-startup status:", font=("Arial", 12), bg="#ecf0f1").pack(pady=5)
        self.status_label = tk.Label(status_frame, text=status_text,
                                    font=("Arial", 14, "bold"),
                                    fg=status_color, bg="#ecf0f1")
        self.status_label.pack(pady=5)

        # Buttons frame
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=20)

        # Enable button
        enable_btn = tk.Button(buttons_frame, text="Enable Auto-startup",
                              command=self.enable_startup,
                              bg="#27ae60", fg="white",
                              font=("Arial", 11, "bold"),
                              width=15, height=2)
        enable_btn.pack(side="left", padx=10)

        # Disable button
        disable_btn = tk.Button(buttons_frame, text="Disable Auto-startup",
                               command=self.disable_startup,
                               bg="#e74c3c", fg="white",
                               font=("Arial", 11, "bold"),
                               width=15, height=2)
        disable_btn.pack(side="left", padx=10)

        # System-specific info
        if platform.system() == "Darwin":
            info_text = ("When enabled, VNC QR Server will start automatically\n"
                        "when you log into macOS.\n"
                        "Uses LaunchAgent in ~/Library/LaunchAgents/")
        elif platform.system() == "Windows":
            info_text = ("When enabled, VNC QR Server will start automatically\n"
                        "when you log into Windows.\n"
                        "Uses Registry entry in HKEY_CURRENT_USER\\...\\Run")
        else:
            info_text = f"Auto-startup not supported on {platform.system()}"

        info_label = tk.Label(self.root, text=info_text,
                             font=("Arial", 9), fg="#7f8c8d")
        info_label.pack(pady=15)

    def enable_startup(self):
        """Handle enable startup button click."""
        if self.startup_manager.enable_startup():
            messagebox.showinfo("Success", "Auto-startup enabled successfully!")
            self.update_status()
        else:
            messagebox.showerror("Error", "Failed to enable auto-startup.")

    def disable_startup(self):
        """Handle disable startup button click."""
        if self.startup_manager.disable_startup():
            messagebox.showinfo("Success", "Auto-startup disabled successfully!")
            self.update_status()
        else:
            messagebox.showerror("Error", "Failed to disable auto-startup.")

    def update_status(self):
        """Update the status display."""
        current_status = self.startup_manager.is_startup_enabled()
        status_text = "ENABLED" if current_status else "DISABLED"
        status_color = "#27ae60" if current_status else "#e74c3c"

        self.status_label.config(text=status_text, fg=status_color)

    def run(self):
        """Start the GUI."""
        self.root.mainloop()

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Command line mode
        startup_manager = StartupManager()

        if sys.argv[1] == "enable":
            if startup_manager.enable_startup():
                print("SUCCESS: Auto-startup enabled")
            else:
                print("ERROR: Failed to enable auto-startup")

        elif sys.argv[1] == "disable":
            if startup_manager.disable_startup():
                print("SUCCESS: Auto-startup disabled")
            else:
                print("ERROR: Failed to disable auto-startup")

        elif sys.argv[1] == "status":
            status = startup_manager.is_startup_enabled()
            print(f"Auto-startup: {'ENABLED' if status else 'DISABLED'}")

        else:
            print("Usage: startup_utility.py [enable|disable|status]")

    else:
        # GUI mode
        app = StartupGUI()
        app.run()

if __name__ == "__main__":
    main()
