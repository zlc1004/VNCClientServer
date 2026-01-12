"""
CLI VNC handling for Tkinter GUI app
"""

import threading
import time

class CLIVNCHandler:
    def __init__(self, app):
        self.app = app

    def handle_vnc_request(self, vnc_data):
        """Handle VNC connection request from web interface."""
        if vnc_data is None:
            # Disconnect request
            return self.disconnect_vnc()

        # Connect request
        ip = vnc_data.get('ip')
        port = vnc_data.get('port', 5900)
        username = vnc_data.get('username')
        password = vnc_data.get('password', '')
        selected_client = vnc_data.get('client')  # Get selected VNC client
        fullscreen = vnc_data.get('fullscreen', False)  # Get fullscreen option

        if not all([ip, port, username]):
            print("Invalid VNC connection data")
            self.app.update_status("Invalid VNC connection data")
            return False

        # Update status
        client_info = f" using {selected_client}" if selected_client else ""
        self.app.update_status(f"Connecting to VNC{client_info}...")

        # Start VNC connection in separate thread
        vnc_thread = threading.Thread(target=self._connect_vnc_thread,
                                     args=(ip, port, username, password, selected_client, fullscreen))
        vnc_thread.daemon = True
        vnc_thread.start()

        return True

    def _connect_vnc_thread(self, ip, port, username, password, selected_client=None, fullscreen=False):
        """Connect to VNC in separate thread."""
        try:
            # Attempt connection with selected client and fullscreen option
            success = self.app.vnc_connector.connect(ip, port, username, password, selected_client, fullscreen)

            if success:
                # Connection successful - hide QR window
                client_info = f" ({selected_client})" if selected_client else ""
                self.app.update_status(f"VNC client launched for {ip}:{port}{client_info}")
                self.app.hide_window()
                self.app.web_server.notify_vnc_status('connected')

                # Monitor connection
                self._monitor_vnc_connection()

            else:
                client_error = f" ({selected_client})" if selected_client else ""
                self.app.update_status(f"Failed to start VNC client{client_error}")
                self.app.web_server.notify_vnc_status('failed')

        except Exception as e:
            print(f"VNC connection error: {e}")
            self.app.update_status(f"VNC error: {str(e)[:50]}...")
            self.app.web_server.notify_vnc_status('failed')

    def _monitor_vnc_connection(self):
        """Monitor VNC connection status."""
        try:
            while self.app.vnc_connector.is_connected():
                time.sleep(2)  # Check every 2 seconds

            # Connection ended - show QR window
            print("VNC connection ended")
            self.app.show_window()
            self.app.update_status("VNC client disconnected")
            self.app.web_server.notify_vnc_status('disconnected')

        except Exception as e:
            print(f"Error monitoring VNC connection: {e}")

    def disconnect_vnc(self):
        """Disconnect VNC and return to normal mode."""
        try:
            self.app.vnc_connector.disconnect()
            self.app.show_window()
            self.app.update_status("VNC client stopped")
            self.app.web_server.notify_vnc_status('disconnected')
            return True

        except Exception as e:
            print(f"Error disconnecting VNC: {e}")
            self.app.update_status("Error stopping VNC client")
            return False
