"""
VNC handling methods for GUI app
"""

import tkinter as tk
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
        self.app.root.after(0, lambda: self.update_status("Connecting to VNC..."))
        
        # Start VNC connection in separate thread
        vnc_thread = threading.Thread(target=self._connect_vnc_thread, 
                                     args=(ip, port, username, password))
        vnc_thread.daemon = True
        vnc_thread.start()
        
        return True
        
    def _connect_vnc_thread(self, ip, port, username, password):
        """Connect to VNC in separate thread."""
        try:
            success = self.app.vnc_connector.connect(ip, port, username, password)
            
            if success:
                # Switch to VNC mode
                self.app.root.after(0, self.switch_to_vnc_mode)
                self.app.web_server.notify_vnc_status('connected')
            else:
                self.app.root.after(0, lambda: self.update_status("VNC connection failed"))
                self.app.web_server.notify_vnc_status('failed')
                
        except Exception as e:
            print(f"VNC connection error: {e}")
            self.app.root.after(0, lambda: self.update_status(f"VNC error: {str(e)}"))
            self.app.web_server.notify_vnc_status('failed')
            
    def switch_to_vnc_mode(self):
        """Switch display to VNC mode."""
        # Hide QR code
        self.app.qr_frame.pack_forget()
        
        # Create VNC display frame
        self.app.vnc_frame = tk.Frame(self.app.root, bg='black')
        self.app.vnc_frame.pack(fill='both', expand=True)
        
        # VNC status/placeholder
        vnc_label = tk.Label(self.app.vnc_frame, 
                           text="🖥️ VNC Connected\n\nVNC session is running\nPress ESC to return to QR code", 
                           font=('Arial', 18, 'bold'),
                           fg='white', bg='black')
        vnc_label.pack(expand=True)
        
        # Bind escape key to return to QR mode
        self.app.root.bind('<Escape>', lambda e: self.disconnect_vnc())
        
        self.app.vnc_mode = True
        self.app.web_server.notify_vnc_status('connected')
        
    def disconnect_vnc(self):
        """Disconnect VNC and return to QR mode."""
        try:
            self.app.vnc_connector.disconnect()
        except Exception as e:
            print(f"Error disconnecting VNC: {e}")
        
        # Switch back to QR mode
        if hasattr(self.app, 'vnc_frame'):
            self.app.vnc_frame.destroy()
            
        # Show QR code again
        self.app.qr_frame.pack(fill='both', expand=True)
        
        # Unbind escape key
        self.app.root.unbind('<Escape>')
        
        self.update_status("Disconnected from VNC")
        self.app.vnc_mode = False
        self.app.web_server.notify_vnc_status('disconnected')
        
        return True
        
    def update_status(self, message):
        """Update status message."""
        if hasattr(self.app, 'status_label'):
            self.app.status_label.config(text=message)
        print(f"Status: {message}")
