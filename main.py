#!/usr/bin/env python3
"""
VNC QR Server Application
A fullscreen application that shows a QR code to connect via web browser
and provides VNC client functionality using system VNC clients.
"""

from threading import Thread
import sys
import os

from gui_app import VNCQRApp
from web_server import WebServer
from config_manager import ConfigManager

def main():
    """Main application entry point."""
    try:
        print("Starting VNC QR Server...")

        # Initialize configuration manager
        print("Initializing configuration...")
        config_manager = ConfigManager()

        # Start web server in background thread
        print("Starting web server...")
        web_server = WebServer(config_manager)
        web_thread = Thread(target=web_server.run, daemon=True)
        web_thread.start()

        # Give web server time to start
        import time
        time.sleep(1)
        print("Web server started")

        # Create and run Tkinter GUI application
        print("Creating Tkinter GUI application...")
        app = VNCQRApp(config_manager, web_server)

        # Set shutdown callback for graceful shutdown from web interface
        def shutdown_application():
            print("Shutdown requested from web interface")
            try:
                app.exit_app()
            except:
                sys.exit(0)

        web_server.set_shutdown_callback(shutdown_application)

        print("Starting Tkinter GUI...")
        app.run()

    except KeyboardInterrupt:
        print("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
