import json
import os
from typing import Dict, List, Any

class ConfigManager:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}")

        # Default configuration
        return {
            'settings': {
                'auto_run': False
            },
            'saved_servers': []
        }

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving config file: {e}")

    def get_settings(self) -> Dict[str, Any]:
        """Get application settings."""
        return self.config.get('settings', {})

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        return self.config.get('settings', {}).get(key, default)

    def save_settings(self, settings: Dict[str, Any]):
        """Save application settings."""
        if 'settings' not in self.config:
            self.config['settings'] = {}
        self.config['settings'].update(settings)
        self.save_config()

    def get_saved_servers(self) -> List[Dict[str, Any]]:
        """Get list of saved VNC servers."""
        return self.config.get('saved_servers', [])

    def save_server(self, server_data: Dict[str, Any]):
        """Save a VNC server configuration."""
        if 'saved_servers' not in self.config:
            self.config['saved_servers'] = []

        # Check if server already exists (by IP and port)
        existing_server = None
        for i, server in enumerate(self.config['saved_servers']):
            if (server.get('ip') == server_data.get('ip') and
                server.get('port') == server_data.get('port')):
                existing_server = i
                break

        if existing_server is not None:
            # Update existing server
            self.config['saved_servers'][existing_server].update(server_data)
        else:
            # Add new server
            self.config['saved_servers'].append(server_data)

        self.save_config()

    def delete_server(self, server_data: Dict[str, Any]):
        """Delete a saved VNC server."""
        if 'saved_servers' not in self.config:
            return

        # Find and remove server
        self.config['saved_servers'] = [
            server for server in self.config['saved_servers']
            if not (server.get('ip') == server_data.get('ip') and
                   server.get('port') == server_data.get('port'))
        ]

        self.save_config()

    def setup_autostart(self, enable: bool = True):
        """Setup application to run at system startup (Windows only)."""
        import platform
        import sys

        system = platform.system()

        if system == "Windows":
            return self._setup_windows_autostart(enable)
        else:
            print(f"Auto-startup not supported on {system}")
            return False

    def is_autostart_supported(self):
        """Check if auto-startup is supported on this platform."""
        import platform
        return platform.system() == "Windows"

    def _setup_windows_autostart(self, enable: bool = True):
        """Setup Windows startup via registry."""
        try:
            import winreg
            import sys

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "VNCQRServer"
            app_path = sys.executable + " " + os.path.abspath(__file__)

            if enable:
                # Add to startup
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                                   winreg.KEY_SET_VALUE) as key:
                    winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                # Remove from startup
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                                       winreg.KEY_SET_VALUE) as key:
                        winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass  # Key doesn't exist, nothing to delete

        except Exception as e:
            print(f"Error setting up Windows autostart: {e}")
            return False

        return True
