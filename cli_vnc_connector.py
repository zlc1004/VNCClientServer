"""
CLI VNC Connector
Uses official VNC client applications via command line interface
"""

import subprocess
import sys
import os
import platform
import shutil
import glob
from threading import Thread
import time

class CLIVNCConnector:
    def __init__(self):
        self.vnc_process = None
        self.connected = False
        self.host = None
        self.port = None
        self.selected_client = None
        self.client_executable = None
        self.fullscreen_mode = False

    def connect(self, host, port, username, password=None, selected_client=None, fullscreen=False):
        """Connect to VNC server using selected VNC client."""
        try:
            # Stop any existing connection
            self.disconnect()

            self.host = host
            self.port = port
            self.selected_client = selected_client
            self.fullscreen_mode = fullscreen

            # Get the appropriate VNC client command
            vnc_command = self._get_vnc_command(host, port, username, password, selected_client)

            if not vnc_command:
                print("❌ Selected VNC client not available or no suitable client found")
                return False

            print(f"Starting VNC client: {' '.join(vnc_command[:3])}...")

            # Prepare environment variables if needed
            env = os.environ.copy()
            if hasattr(self, 'client_env_vars') and self.client_env_vars:
                env.update(self.client_env_vars)
                print(f"  Using environment variables: {list(self.client_env_vars.keys())}")

            # Start VNC client in background
            self.vnc_process = subprocess.Popen(
                vnc_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == 'Windows' else 0
            )

            # Give VNC client time to start
            time.sleep(2)

            # Check if process is still running
            if self.vnc_process.poll() is None:
                self.connected = True
                print("✓ VNC client started successfully")

                # Apply fullscreen modifications if requested (Windows only)
                if self.fullscreen_mode and platform.system() == "Windows":
                    fullscreen_thread = Thread(target=self._apply_fullscreen_modifications, daemon=True)
                    fullscreen_thread.start()

                # Monitor VNC client in background
                monitor_thread = Thread(target=self._monitor_vnc_client, daemon=True)
                monitor_thread.start()

                return True
            else:
                print("❌ VNC client failed to start")
                stdout, stderr = self.vnc_process.communicate()
                if stderr:
                    print(f"Error: {stderr.decode().strip()}")
                return False

        except Exception as e:
            print(f"Error starting VNC client: {e}")
            return False

    def _get_vnc_command(self, host, port, username, password, selected_client=None):
        """Get appropriate VNC client command based on selection or platform detection."""
        system = platform.system()

        # Construct connection string
        connection_string = f"{host}:{port}"
        if port == 5900:
            connection_string = host  # Default VNC port
        elif port > 5900:
            display_num = port - 5900
            connection_string = f"{host}:{display_num}"

        if system == "Windows":
            return self._get_windows_vnc_command(connection_string, username, password, selected_client)
        elif system == "Darwin":  # macOS
            return self._get_macos_vnc_command(connection_string, username, password, selected_client)
        else:  # Linux and others
            return self._get_linux_vnc_command(connection_string, username, password, selected_client)

    def _get_windows_vnc_command(self, connection_string, username, password, selected_client=None):
        """Get VNC command for Windows."""
        # Define available Windows VNC clients
        clients = {
            'tightvnc': {
                'name': 'TightVNC Viewer',
                'executable': 'tvnviewer.exe',
                'locations': [
                    'C:\\Program Files\\TightVNC\\tvnviewer.exe',
                    'C:\\Program Files (x86)\\TightVNC\\tvnviewer.exe'
                ],
                'args': ['-host', connection_string] + (['-password', password] if password else []),
                'supports_password': True,
                'auth_method': 'cli_param'
            },
            'realvnc': {
                'name': 'RealVNC Viewer',
                'executable': 'vncviewer.exe',
                'locations': [
                    'C:\\Program Files\\RealVNC\\VNC Viewer\\vncviewer.exe',
                    'C:\\Program Files (x86)\\RealVNC\\VNC Viewer\\vncviewer.exe'
                ],
                'args': [connection_string],
                'supports_password': False,  # RealVNC CLI doesn't support password parameter
                'auth_method': 'manual'
            },
            'tigervnc': {
                'name': 'TigerVNC Viewer',
                'executable': 'vncviewer*.exe',  # Pattern for search
                'locations': [],  # Will be populated dynamically
                'search_patterns': [
                    'vncviewer64-*.*.*.exe',
                    'vncviewer-*.*.*.exe',
                    '**/vncviewer64-*.*.*.exe',
                    '**/vncviewer-*.*.*.exe'
                ],
                'args': [connection_string],
                'supports_password': True,  # Via environment variables
                'auth_method': 'env_vars',
                'env_vars': {
                    'VNC_USERNAME': username,
                    'VNC_PASSWORD': password
                }
            },
            'ultravnc': {
                'name': 'UltraVNC',
                'executable': 'vncviewer.exe',
                'locations': [
                    'C:\\Program Files\\uvnc bvba\\UltraVNC\\vncviewer.exe',
                    'C:\\Program Files (x86)\\uvnc bvba\\UltraVNC\\vncviewer.exe',
                    'C:\\Program Files\\UltraVNC\\vncviewer.exe',  # Legacy path
                    'C:\\Program Files (x86)\\UltraVNC\\vncviewer.exe'  # Legacy path
                ],
                'args': [connection_string] + (['-password', password] if password else []),
                'supports_password': True,
                'auth_method': 'cli_param'
            }
        }

        # If specific client selected, try only that one
        if selected_client and selected_client in clients:
            client = clients[selected_client]
            return self._try_client(client)

        # Otherwise try all clients in order of preference (TigerVNC first)
        for client_key in ['tigervnc', 'tightvnc', 'realvnc', 'ultravnc']:
            client = clients[client_key]
            result = self._try_client(client)
            if result:
                return result

        return None

    def _try_client(self, client):
        """Try to find and use a specific VNC client."""
        executable_path = None

        # Check if client has search patterns (for TigerVNC standalone files)
        if 'search_patterns' in client:
            executable_path = self._find_tigervnc_executable(client['search_patterns'])
        else:
            # Check if executable exists in PATH
            if shutil.which(client['executable']):
                executable_path = client['executable']
            else:
                # Check specific locations
                for location in client['locations']:
                    if os.path.exists(location):
                        executable_path = location
                        break

        if executable_path:
            cmd = [executable_path] + client['args']
            self.client_executable = os.path.basename(executable_path)

            # Store environment variables if client uses them
            if client.get('auth_method') == 'env_vars' and 'env_vars' in client:
                self.client_env_vars = client['env_vars']
            else:
                self.client_env_vars = None

            return [arg for arg in cmd if arg]  # Filter empty args

        return None

    def _find_tigervnc_executable(self, search_patterns):
        """Find TigerVNC standalone executable using search patterns."""
        try:
            # Search in current directory and subdirectories
            for pattern in search_patterns:
                matches = glob.glob(pattern, recursive=True)
                if matches:
                    # Return the first match, preferring 64-bit version
                    matches.sort(reverse=True)  # This puts vncviewer64- before vncviewer-
                    executable_path = matches[0]
                    print(f"Found TigerVNC executable: {executable_path}")
                    return os.path.abspath(executable_path)

            return None

        except Exception as e:
            print(f"Error searching for TigerVNC executable: {e}")
            return None

    def _get_macos_vnc_command(self, connection_string, username, password, selected_client=None):
        """Get VNC command for macOS."""
        # macOS built-in Screen Sharing
        vnc_url = f"vnc://{connection_string}"
        if username and password:
            vnc_url = f"vnc://{username}:{password}@{connection_string}"
        elif username:
            vnc_url = f"vnc://{username}@{connection_string}"

        self.client_executable = "Screen Sharing"
        return ['open', vnc_url]

    def _get_linux_vnc_command(self, connection_string, username, password, selected_client=None):
        """Get VNC command for Linux."""
        clients = {
            'remmina': {
                'name': 'Remmina',
                'executable': 'remmina',
                'args': ['-c', f'vnc://{connection_string}'],
                'supports_password': True,
                'auth_method': 'url_based'
            },
            'tigervnc': {
                'name': 'TigerVNC Viewer',
                'executable': 'vncviewer',
                'args': [connection_string],
                'supports_password': True,
                'auth_method': 'env_vars',
                'env_vars': {
                    'VNC_USERNAME': username,
                    'VNC_PASSWORD': password
                }
            },
            'vinagre': {
                'name': 'Vinagre',
                'executable': 'vinagre',
                'args': [f'vnc://{connection_string}'],
                'supports_password': True,
                'auth_method': 'url_based'
            }
        }

        # If specific client selected, try only that one
        if selected_client and selected_client in clients:
            client = clients[selected_client]
            if shutil.which(client['executable']):
                self.client_executable = client['executable']
                return [client['executable']] + client['args']

        # Otherwise try all clients in order
        for client_key in ['remmina', 'tigervnc', 'vinagre']:
            client = clients[client_key]
            if shutil.which(client['executable']):
                self.client_executable = client['executable']

                # Handle environment variables for TigerVNC
                if client.get('auth_method') == 'env_vars' and 'env_vars' in client:
                    self.client_env_vars = client['env_vars']
                else:
                    self.client_env_vars = None

                return [client['executable']] + client['args']

        return None

    def _apply_fullscreen_modifications(self):
        """Apply fullscreen, always-on-top, and borderless modifications to VNC client window."""
        try:
            # Only run on Windows
            if platform.system() != "Windows":
                print("Fullscreen modifications only supported on Windows")
                return

            # Import Windows-specific modules
            import win32con
            import win32gui
            from pywinauto.application import Application

            print("Applying fullscreen modifications to VNC client...")
            time.sleep(3)  # Wait for VNC window to appear

            # Connect to the running VNC process
            app = Application(backend="win32").connect(process=self.vnc_process.pid)

            # Get the main window
            main_window = app.top_window()
            hwnd = main_window.handle

            print(f"Found VNC window handle: {hwnd}")

            # Remove title bar and borders
            current_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            new_style = current_style & ~win32con.WS_CAPTION & ~win32con.WS_THICKFRAME
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)

            # Set window to always on top
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED
            )

            # Maximize the window (fullscreen)
            main_window.maximize()

            print("✓ VNC client window: fullscreen, always on top, no title bar!")

        except ImportError:
            print("⚠️ pywinauto or pywin32 not installed - fullscreen mode unavailable")
        except Exception as e:
            print(f"Error applying fullscreen modifications: {e}")

    def _monitor_vnc_client(self):
        """Monitor VNC client process."""
        try:
            while self.connected and self.vnc_process:
                # Check if process is still running
                if self.vnc_process.poll() is not None:
                    print("VNC client process ended")
                    self.connected = False
                    break
                time.sleep(1)
        except Exception as e:
            print(f"Error monitoring VNC client: {e}")
            self.connected = False

    def disconnect(self):
        """Disconnect from VNC server and kill all VNC client processes."""
        self.connected = False

        # First, try to terminate our known process
        if self.vnc_process:
            try:
                print("Terminating VNC client process...")
                self.vnc_process.terminate()

                # Wait for process to end gracefully
                try:
                    self.vnc_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print("Force killing VNC client process...")
                    self.vnc_process.kill()

            except Exception as e:
                print(f"Error terminating VNC process: {e}")

            self.vnc_process = None

        # Additionally, kill any remaining VNC client processes by name
        self._kill_vnc_processes()

        print("VNC disconnection complete")

    def _kill_vnc_processes(self):
        """Kill VNC client processes by executable name."""
        try:
            system = platform.system()
            vnc_executables = []

            if system == "Windows":
                vnc_executables = ['tvnviewer.exe', 'vncviewer.exe']  # Covers TigerVNC, RealVNC, UltraVNC
            elif system == "Darwin":
                # macOS Screen Sharing doesn't need process killing
                return
            else:  # Linux
                vnc_executables = ['remmina', 'vncviewer', 'vinagre', 'krdc']  # vncviewer covers TigerVNC

            for executable in vnc_executables:
                if system == "Windows":
                    # Use taskkill on Windows
                    try:
                        subprocess.run(['taskkill', '/F', '/IM', executable],
                                     capture_output=True, check=False)
                        print(f"Killed {executable} processes")
                    except Exception as e:
                        pass  # Silently continue if process not found
                else:
                    # Use pkill on Linux/Unix
                    try:
                        subprocess.run(['pkill', '-f', executable],
                                     capture_output=True, check=False)
                        print(f"Killed {executable} processes")
                    except Exception as e:
                        pass  # Silently continue if process not found

        except Exception as e:
            print(f"Error killing VNC processes: {e}")

    def is_connected(self):
        """Check if VNC client is connected."""
        if not self.connected or not self.vnc_process:
            return False

        # Check if process is still running
        if self.vnc_process.poll() is not None:
            self.connected = False
            return False

        return True

    def get_available_clients(self):
        """Get list of available VNC clients on the system."""
        system = platform.system()
        available = []

        if system == "Windows":
            clients = {
                'tightvnc': {
                    'name': 'TightVNC Viewer',
                    'executable': 'tvnviewer.exe',
                    'locations': [
                        'C:\\Program Files\\TightVNC\\tvnviewer.exe',
                        'C:\\Program Files (x86)\\TightVNC\\tvnviewer.exe'
                    ],
                    'supports_password': True
                },
                'realvnc': {
                    'name': 'RealVNC Viewer',
                    'executable': 'vncviewer.exe',
                    'locations': [
                        'C:\\Program Files\\RealVNC\\VNC Viewer\\vncviewer.exe',
                        'C:\\Program Files (x86)\\RealVNC\\VNC Viewer\\vncviewer.exe'
                    ],
                    'supports_password': False
                },
                'tigervnc': {
                    'name': 'TigerVNC Viewer',
                    'executable': 'vncviewer*.exe',
                    'search_patterns': [
                        'vncviewer64-*.*.*.exe',
                        'vncviewer-*.*.*.exe',
                        '**/vncviewer64-*.*.*.exe',
                        '**/vncviewer-*.*.*.exe'
                    ],
                    'supports_password': True
                },
                'ultravnc': {
                    'name': 'UltraVNC',
                    'executable': 'vncviewer.exe',
                    'locations': [
                        'C:\\Program Files\\uvnc bvba\\UltraVNC\\vncviewer.exe',
                        'C:\\Program Files (x86)\\uvnc bvba\\UltraVNC\\vncviewer.exe',
                        'C:\\Program Files\\UltraVNC\\vncviewer.exe',  # Legacy path
                        'C:\\Program Files (x86)\\UltraVNC\\vncviewer.exe'  # Legacy path
                    ],
                    'supports_password': True
                }
            }

            # Check clients in preferred order (TigerVNC first)
            for client_id in ['tigervnc', 'tightvnc', 'realvnc', 'ultravnc']:
                if client_id not in clients:
                    continue

                client_info = clients[client_id]
                client_found = False

                # Special handling for TigerVNC with search patterns
                if 'search_patterns' in client_info:
                    tigervnc_path = self._find_tigervnc_executable(client_info['search_patterns'])
                    if tigervnc_path:
                        client_found = True
                else:
                    # Check if executable exists in PATH
                    if shutil.which(client_info['executable']):
                        client_found = True
                    else:
                        # Check specific locations
                        for location in client_info['locations']:
                            if os.path.exists(location):
                                client_found = True
                                break

                if client_found:
                    available.append({
                        'id': client_id,
                        'name': client_info['name'],
                        'supports_password': client_info['supports_password']
                    })

        elif system == "Darwin":
            available.append({
                'id': 'macos_screen_sharing',
                'name': 'macOS Screen Sharing (built-in)',
                'supports_password': True
            })

        else:  # Linux
            clients = {
                'remmina': {'name': 'Remmina', 'supports_password': True},
                'tigervnc': {'name': 'TigerVNC Viewer', 'supports_password': True},
                'vinagre': {'name': 'Vinagre', 'supports_password': True}
            }

            for client_id, client_info in clients.items():
                if shutil.which(client_id):
                    available.append({
                        'id': client_id,
                        'name': client_info['name'],
                        'supports_password': client_info['supports_password']
                    })

        return available
