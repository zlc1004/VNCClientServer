import sys
import os
from threading import Thread
import tkinter as tk
from tkinter import messagebox

try:
    from pyVNC.Client import Client
except ImportError as e:
    print(f"Error importing pyVNC: {e}")
    print("VNC functionality will be limited - install pyVNC with: pip install -e ./pyVNC/")
    Client = None

class VNCConnector:
    def __init__(self):
        self.vnc_client = None
        self.connection_thread = None
        self.connected = False

    def connect(self, host, port, username, password=None):
        """Connect to VNC server."""
        if Client is None:
            messagebox.showerror("Error", "pyVNC module not available!")
            return False

        try:
            # Stop any existing connection
            self.disconnect()

            # Create new VNC client
            self.vnc_client = Client(
                host=host,
                port=int(port),
                password=password,
                depth=32,
                fast=True,
                shared=True,
                gui=True,
                array=False
            )

            # Start connection in a separate thread
            self.connection_thread = Thread(target=self._run_vnc_client, daemon=True)
            self.connection_thread.start()

            self.connected = True
            return True

        except Exception as e:
            print(f"Error connecting to VNC server: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")
            return False

    def _run_vnc_client(self):
        """Run the VNC client in a separate thread."""
        try:
            if self.vnc_client:
                self.vnc_client.start()
        except Exception as e:
            print(f"Error in VNC client thread: {e}")
            self.connected = False

    def disconnect(self):
        """Disconnect from VNC server."""
        if self.vnc_client:
            try:
                # Stop the VNC client
                if hasattr(self.vnc_client, 'stop'):
                    self.vnc_client.stop()
                elif hasattr(self.vnc_client, 'screen') and hasattr(self.vnc_client.screen, 'protocol'):
                    # Try to close the protocol connection
                    if hasattr(self.vnc_client.screen.protocol, 'transport'):
                        self.vnc_client.screen.protocol.transport.loseConnection()
            except Exception as e:
                print(f"Error disconnecting VNC client: {e}")

        self.vnc_client = None
        self.connected = False

    def is_connected(self):
        """Check if VNC client is connected."""
        return self.connected

    def send_key(self, key):
        """Send a key to the VNC server."""
        if self.vnc_client and self.connected:
            try:
                self.vnc_client.send_key(key)
            except Exception as e:
                print(f"Error sending key: {e}")

    def send_mouse_click(self, x, y, button=1):
        """Send a mouse click to the VNC server."""
        if self.vnc_client and self.connected:
            try:
                # This would need to be implemented based on pyVNC's mouse handling
                if hasattr(self.vnc_client.screen, 'protocol'):
                    protocol = self.vnc_client.screen.protocol
                    if hasattr(protocol, 'pointer_event'):
                        protocol.pointer_event(x, y, buttonmask=button)
            except Exception as e:
                print(f"Error sending mouse click: {e}")

class VNCWindow:
    """Separate window for VNC display when connected."""

    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.window = None

    def create_vnc_window(self):
        """Create a separate fullscreen window for VNC display."""
        if self.window:
            return

        self.window = tk.Toplevel()
        self.window.title("VNC Connection")
        self.window.attributes('-fullscreen', True)
        self.window.attributes('-topmost', True)
        self.window.configure(bg='black')

        # Bind escape to close VNC window
        self.window.bind('<Escape>', self.close_vnc_window)

        # Create a frame for VNC content
        self.vnc_frame = tk.Frame(self.window, bg='black')
        self.vnc_frame.pack(fill='both', expand=True)

        # Add instructions
        instructions = tk.Label(
            self.vnc_frame,
            text="VNC Connection Active\nPress ESC to return to main application",
            font=('Arial', 16),
            fg='white',
            bg='black'
        )
        instructions.pack(expand=True)

    def close_vnc_window(self, event=None):
        """Close VNC window and return to main application."""
        if self.window:
            self.window.destroy()
            self.window = None
        # Restore main application window
        if hasattr(self.parent_app, 'restore_from_qr'):
            self.parent_app.restore_from_qr()

    def show_vnc_display(self):
        """Show the VNC display in the window."""
        self.create_vnc_window()

    def hide_vnc_display(self):
        """Hide the VNC display window."""
        if self.window:
            self.window.withdraw()
