import tkinter as tk
from tkinter import ttk, messagebox
import qrcode
from PIL import Image, ImageTk
from network_utils import get_local_ip
from cli_vnc_connector import CLIVNCConnector
import threading
import json

class VNCQRApp:
    def __init__(self, config_manager, web_server):
        self.config_manager = config_manager
        self.web_server = web_server
        self.vnc_connector = CLIVNCConnector()
        self.vnc_mode = False
        self.vnc_window = None

        # Set callback for web server VNC requests
        self.web_server.set_vnc_callback(self.handle_vnc_request)

        # Create main window
        self.root = tk.Tk()
        self.setup_window()
        self.create_qr_display()

        # Show available VNC clients
        self.show_vnc_client_info()

    def setup_window(self):
        """Configure the main window to be fullscreen, always on top, and without decorations."""
        try:
            self.root.title("VNC QR Server")

            # Start in windowed mode, then go fullscreen to avoid crashes
            self.root.geometry("800x600")
            self.root.configure(bg='#2c3e50')

            # Update display
            self.root.update()

            # Now go fullscreen
            self.root.attributes('-fullscreen', True)
            self.root.attributes('-topmost', True)
            self.root.overrideredirect(True)  # Remove window decorations

            # Bind escape key to exit
            self.root.bind('<Escape>', self.exit_app)

        except Exception as e:
            print(f"Error setting up window: {e}")
            # Fallback to basic window
            self.root.title("VNC QR Server")
            self.root.geometry("800x600")
            self.root.configure(bg='#2c3e50')

    def create_qr_display(self):
        """Create simple QR code display."""
        # Main container
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True)

        # QR Code section in the center
        self.qr_frame = tk.Frame(main_frame, bg='#2c3e50')
        self.qr_frame.pack(expand=True, fill='both')

        self.create_qr_section(self.qr_frame)

    def create_qr_section(self, parent):
        """Create QR code display section."""
        # Generate QR code
        local_ip = get_local_ip()
        qr_url = f"http://{local_ip}:8080"

        qr = qrcode.QRCode(version=1, box_size=15, border=5)
        qr.add_data(qr_url)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="white", back_color="#2c3e50")
        qr_img = qr_img.resize((500, 500), Image.Resampling.LANCZOS)
        self.qr_photo = ImageTk.PhotoImage(qr_img)

        # QR Code label
        self.qr_label = tk.Label(parent, image=self.qr_photo, bg='#2c3e50')
        self.qr_label.pack(expand=True)

        # URL label
        self.url_label = tk.Label(parent, text=qr_url, font=('Arial', 20, 'bold'),
                                fg='white', bg='#2c3e50')
        self.url_label.pack(pady=20)

        # Status label
        self.status_label = tk.Label(parent, text="Scan QR code to access VNC control",
                                   font=('Arial', 14), fg='#bdc3c7', bg='#2c3e50')
        self.status_label.pack(pady=10)

        # VNC client info
        self.vnc_info_label = tk.Label(parent, text="",
                                     font=('Arial', 10), fg='#95a5a6', bg='#2c3e50')
        self.vnc_info_label.pack(pady=(0, 10))
    def handle_vnc_request(self, vnc_data):
        """Handle VNC connection request from web interface."""
        from cli_vnc_handler import CLIVNCHandler
        if not hasattr(self, 'vnc_handler'):
            self.vnc_handler = CLIVNCHandler(self)
        return self.vnc_handler.handle_vnc_request(vnc_data)

    def show_vnc_client_info(self):
        """Show information about available VNC clients."""
        try:
            available_clients = self.vnc_connector.get_available_clients()
            if available_clients:
                info_text = f"VNC Clients Found: {len(available_clients)}"
                print("Available VNC clients:")
                for client in available_clients:
                    if isinstance(client, dict):
                        password_support = "YES" if client.get('supports_password') else "NO"
                        print(f"  - {client['name']} (Password: {password_support})")
                    else:
                        print(f"  - {client}")
            else:
                info_text = "No VNC clients detected - Install a VNC client"
                print("WARNING: No VNC clients found on system")
                print("Please install one of the following:")
                print("  Windows: TightVNC, RealVNC Viewer, UltraVNC")
                print("  macOS: Built-in Screen Sharing (vnc:// URLs)")
                print("  Linux: remmina, vncviewer, vinagre")

            if hasattr(self, 'vnc_info_label'):
                self.vnc_info_label.config(text=info_text)

        except Exception as e:
            print(f"Error checking VNC clients: {e}")

    def update_status(self, message):
        """Update status message."""
        if hasattr(self, 'status_label'):
            self.status_label.config(text=message)
        print(f"Status: {message}")

    def hide_window(self):
        """Hide the QR code window when VNC is connected."""
        try:
            self.root.withdraw()
            print("QR window hidden")
        except Exception as e:
            print(f"Error hiding window: {e}")

    def show_window(self):
        """Show the QR code window when VNC is disconnected."""
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes('-topmost', True)
            print("QR window shown")
        except Exception as e:
            print(f"Error showing window: {e}")

    def exit_app(self, event=None):
        """Exit the application."""
        try:
            # Disconnect VNC if connected
            if hasattr(self, 'vnc_connector') and self.vnc_connector:
                self.vnc_connector.disconnect()
        except Exception as e:
            print(f"Error disconnecting VNC on exit: {e}")

        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the GUI application."""
        # Bind ESC to exit when not in VNC mode
        self.root.bind('<Escape>', self.exit_app)

        # Set up window closing protocol
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.root.mainloop()

    def exit_app(self, event=None):
        """Exit the application."""
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()
