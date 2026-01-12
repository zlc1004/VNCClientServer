"""
VNC handling methods for Pygame GUI app
"""

import threading
import time

class VNCHandler:
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

        if not all([ip, port, username]):
            print("Invalid VNC connection data")
            return False

        # Update status
        self.update_status("Connecting to VNC...")

        # Start VNC connection in separate thread
        vnc_thread = threading.Thread(target=self._connect_vnc_thread,
                                     args=(ip, port, username, password))
        vnc_thread.daemon = True
        vnc_thread.start()

        return True

    def _connect_vnc_thread(self, ip, port, username, password):
        """Connect to VNC in separate thread."""
        try:
            # Pass pygame screen surface if available
            pygame_surface = getattr(self.app, 'screen', None)
            success = self.app.vnc_connector.connect(ip, port, username, password, pygame_surface)

            if success:
                # Wait a moment for connection to establish
                time.sleep(3)
                # Switch to VNC mode
                self.switch_to_vnc_mode()
                self.app.web_server.notify_vnc_status('connected')
            else:
                self.update_status("VNC connection failed")
                self.app.web_server.notify_vnc_status('failed')

        except Exception as e:
            print(f"VNC connection error: {e}")
            self.update_status(f"VNC error: {str(e)}")
            self.app.web_server.notify_vnc_status('failed')

    def switch_to_vnc_mode(self):
        """Switch display to VNC mode."""
        # Use Pygame app's switch method
        if hasattr(self.app, 'switch_to_vnc_mode'):
            self.app.switch_to_vnc_mode()

        self.app.vnc_mode = True
        self.app.web_server.notify_vnc_status('connected')

    def disconnect_vnc(self):
        """Disconnect VNC and return to QR mode."""
        try:
            self.app.vnc_connector.disconnect()
        except Exception as e:
            print(f"Error disconnecting VNC: {e}")

        # Switch back to QR mode using Pygame app's method
        if hasattr(self.app, 'switch_to_qr_mode'):
            self.app.switch_to_qr_mode()

        self.update_status("Disconnected from VNC")
        self.app.vnc_mode = False
        self.app.web_server.notify_vnc_status('disconnected')

        return True

    def update_status(self, message):
        """Update status message."""
        if hasattr(self.app, 'update_status'):
            self.app.update_status(message)
        print(f"Status: {message}")
