"""
CLI VNC Connector
Uses official VNC client applications via command line interface
"""

import subprocess
import sys
import os
import platform
import shutil
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

    def connect(self, host, port, username, password=None, selected_client=None):
        """Connect to VNC server using selected VNC client."""
        try:
            # Stop any existing connection
            self.disconnect()

            self.host = host
            self.port = port
            self.selected_client = selected_client

            # Get the appropriate VNC client command
            vnc_command = self._get_vnc_command(host, port, username, password, selected_client)

            if not vnc_command:
                print("❌ Selected VNC client not available or no suitable client found")
                return False

            print(f"Starting VNC client: {' '.join(vnc_command[:3])}...")

            # Start VNC client in background
            self.vnc_process = subprocess.Popen(
                vnc_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if platform.system() == 'Windows' else 0
            )

            # Give VNC client time to start
            time.sleep(2)

            # Check if process is still running
            if self.vnc_process.poll() is None:
                self.connected = True
                print("✓ VNC client started successfully")

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
                'supports_password': True
            },
            'realvnc': {
                'name': 'RealVNC Viewer',
                'executable': 'vncviewer.exe',
                'locations': [
                    'C:\\Program Files\\RealVNC\\VNC Viewer\\vncviewer.exe',
                    'C:\\Program Files (x86)\\RealVNC\\VNC Viewer\\vncviewer.exe'
                ],
                'args': [connection_string],
                'supports_password': False  # RealVNC CLI doesn't support password parameter
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
                'supports_password': True
            }
        }

        # If specific client selected, try only that one
        if selected_client and selected_client in clients:
            client = clients[selected_client]
            return self._try_client(client)

        # Otherwise try all clients in order of preference
        for client_key in ['tightvnc', 'realvnc', 'ultravnc']:
            client = clients[client_key]
            result = self._try_client(client)
            if result:
                return result

        return None

    def _try_client(self, client):
        """Try to find and use a specific VNC client."""
        # Check if executable exists in PATH
        if shutil.which(client['executable']):
            cmd = [client['executable']] + client['args']
            self.client_executable = client['executable']
            return [arg for arg in cmd if arg]  # Filter empty args

        # Check specific locations
        for location in client['locations']:
            if os.path.exists(location):
                cmd = [location] + client['args']
                self.client_executable = os.path.basename(location)
                return [arg for arg in cmd if arg]  # Filter empty args

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
                'args': ['-c', f'vnc://{connection_string}']
            },
            'vncviewer': {
                'name': 'TigerVNC Viewer',
                'executable': 'vncviewer',
                'args': [connection_string]
            },
            'vinagre': {
                'name': 'Vinagre',
                'executable': 'vinagre',
                'args': [f'vnc://{connection_string}']
            }
        }

        # If specific client selected, try only that one
        if selected_client and selected_client in clients:
            client = clients[selected_client]
            if shutil.which(client['executable']):
                self.client_executable = client['executable']
                return [client['executable']] + client['args']

        # Otherwise try all clients in order
        for client_key in ['remmina', 'vncviewer', 'vinagre']:
            client = clients[client_key]
            if shutil.which(client['executable']):
                self.client_executable = client['executable']
                return [client['executable']] + client['args']

        return None

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
                vnc_executables = ['tvnviewer.exe', 'vncviewer.exe']
            elif system == "Darwin":
                # macOS Screen Sharing doesn't need process killing
                return
            else:  # Linux
                vnc_executables = ['remmina', 'vncviewer', 'vinagre', 'krdc']

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

            for client_id, client_info in clients.items():
                # Check if executable exists in PATH
                if shutil.which(client_info['executable']):
                    available.append({
                        'id': client_id,
                        'name': client_info['name'],
                        'supports_password': client_info['supports_password']
                    })
                    continue

                # Check specific locations
                for location in client_info['locations']:
                    if os.path.exists(location):
                        available.append({
                            'id': client_id,
                            'name': client_info['name'],
                            'supports_password': client_info['supports_password']
                        })
                        break

        elif system == "Darwin":
            available.append({
                'id': 'macos_screen_sharing',
                'name': 'macOS Screen Sharing (built-in)',
                'supports_password': True
            })

        else:  # Linux
            clients = {
                'remmina': {'name': 'Remmina', 'supports_password': True},
                'vncviewer': {'name': 'TigerVNC Viewer', 'supports_password': True},
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
