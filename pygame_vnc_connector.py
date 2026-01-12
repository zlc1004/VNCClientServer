"""
Enhanced VNC connector that renders directly to Pygame surfaces
"""

import sys
import os
from threading import Thread, Lock
import pygame
import numpy as np
from PIL import Image
import time

try:
    # Import pyVNC using the simplified import system
    import pyVNC
    Client = pyVNC.get_client() if hasattr(pyVNC, 'get_client') else pyVNC.Client

    if Client is not None:
        print("✓ pyVNC imported successfully")
        if hasattr(pyVNC, 'is_available'):
            print(f"  Client available: {pyVNC.is_available()}")
        else:
            print("  Client imported directly")
    else:
        print("❌ pyVNC.Client not available after import")

except ImportError as e:
    print(f"❌ pyVNC package import failed: {e}")
    print("This might be due to:")
    print("  - NumPy compatibility issues")
    print("  - Missing dependencies (twisted, numpy, pygame)")
    print("  - pyVNC not properly installed")
    print("  - Circular import issues")
    print("VNC functionality will be disabled.")
    Client = None

except Exception as e:
    print(f"❌ Unexpected error importing pyVNC: {e}")
    Client = None

class PygameVNCConnector:
    def __init__(self):
        self.vnc_client = None
        self.connection_thread = None
        self.connected = False
        self.screen_data = None
        self.screen_lock = Lock()
        self.pygame_surface = None
        self.vnc_available = Client is not None  # Track if pyVNC is available

    def connect(self, host, port, username, password=None, target_surface=None):
        """Connect to VNC server and render to target surface."""
        if Client is None:
            print("❌ Cannot connect to VNC: pyVNC module not available!")
            print("Please check the startup logs for import errors.")
            return False

        try:
            # Stop any existing connection
            self.disconnect()

            # Store target surface
            self.target_surface = target_surface
            self.vnc_host = host
            self.vnc_port = port

            print(f"Connecting to VNC server {host}:{port}")

            # Try different approaches to get VNC working
            success = self._try_vnc_approaches(host, port, username, password)

            if success:
                self.connected = True
                print("VNC connection established")
                return True
            else:
                print("All VNC connection approaches failed")
                return False

        except Exception as e:
            print(f"Error connecting to VNC server: {e}")
            return False

    def _try_vnc_approaches(self, host, port, username, password):
        """Try different approaches to establish VNC connection."""

        # Approach 1: Try with GUI disabled for screen capture
        try:
            print("Trying VNC with GUI disabled...")
            self.vnc_client = Client(
                host=host,
                port=int(port),
                password=password,
                depth=32,
                fast=True,
                shared=True,
                gui=False,
                array=False
            )

            self._setup_screen_capture()
            self.connection_thread = Thread(target=self._run_vnc_client, daemon=True)
            self.connection_thread.start()
            time.sleep(3)

            # Check if we got a connection
            if self.vnc_client and hasattr(self.vnc_client, 'screen'):
                return True

        except Exception as e:
            print(f"Approach 1 failed: {e}")

        # Approach 2: Use GUI mode but try to manage the window
        try:
            print("Trying VNC with GUI enabled...")
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

            self.connection_thread = Thread(target=self._run_vnc_client, daemon=True)
            self.connection_thread.start()
            time.sleep(3)

            return True

        except Exception as e:
            print(f"Approach 2 failed: {e}")

        return False

    def _setup_screen_capture(self):
        """Set up screen capture from VNC client."""
        try:
            # Hook into VNC client's screen updates
            if hasattr(self.vnc_client, 'screen'):
                # Try to set up screen update callback
                original_update = getattr(self.vnc_client.screen, 'update', None)
                if original_update:
                    def wrapped_update(*args, **kwargs):
                        result = original_update(*args, **kwargs)
                        self._capture_screen()
                        return result
                    self.vnc_client.screen.update = wrapped_update
        except Exception as e:
            print(f"Error setting up screen capture: {e}")

    def _run_vnc_client(self):
        """Run the VNC client in a separate thread."""
        try:
            if self.vnc_client:
                print("Starting VNC client...")
                self.vnc_client.start()

                # Start screen capture loop
                self._screen_capture_loop()
        except Exception as e:
            print(f"Error in VNC client thread: {e}")
            self.connected = False

    def _screen_capture_loop(self):
        """Continuously capture screen updates."""
        while self.connected and self.vnc_client:
            try:
                time.sleep(0.1)  # Capture at ~10 FPS
                self._capture_screen()
            except Exception as e:
                print(f"Error in screen capture loop: {e}")
                break

    def _capture_screen(self):
        """Capture current screen from VNC client."""
        try:
            if self.vnc_client and hasattr(self.vnc_client, 'screen'):
                # Try to get screen data from VNC client
                screen = self.vnc_client.screen
                if hasattr(screen, 'save'):
                    # Save screen to memory buffer
                    import io
                    buffer = io.BytesIO()
                    screen.save(buffer, format='PNG')
                    buffer.seek(0)

                    # Load as PIL image
                    pil_image = Image.open(buffer)

                    # Convert to Pygame surface
                    mode = pil_image.mode
                    size = pil_image.size
                    data = pil_image.tobytes()

                    with self.screen_lock:
                        self.pygame_surface = pygame.image.fromstring(data, size, mode)

        except Exception as e:
            # Silently handle errors to avoid spam
            pass

    def on_screen_update(self, screen_data):
        """Callback for when VNC screen is updated."""
        try:
            with self.screen_lock:
                # Convert screen data to pygame surface
                if isinstance(screen_data, np.ndarray):
                    # Convert numpy array to PIL Image
                    if screen_data.shape[2] == 4:  # RGBA
                        mode = 'RGBA'
                    else:  # RGB
                        mode = 'RGB'

                    pil_image = Image.fromarray(screen_data, mode)

                    # Convert PIL image to Pygame surface
                    mode = pil_image.mode
                    size = pil_image.size
                    data = pil_image.tobytes()

                    self.pygame_surface = pygame.image.fromstring(data, size, mode)

        except Exception as e:
            print(f"Error processing screen update: {e}")

    def get_screen_surface(self):
        """Get the current screen as a pygame surface."""
        with self.screen_lock:
            return self.pygame_surface

    def disconnect(self):
        """Disconnect from VNC server."""
        if self.vnc_client:
            try:
                print("Disconnecting from VNC...")
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
        with self.screen_lock:
            self.pygame_surface = None

    def is_connected(self):
        """Check if VNC client is connected."""
        return self.connected and self.vnc_client is not None

    def send_key_event(self, key_code, key_down=True):
        """Send a key event to the VNC server."""
        if self.vnc_client and self.connected:
            try:
                # Send key event to VNC server
                if hasattr(self.vnc_client.screen, 'protocol'):
                    protocol = self.vnc_client.screen.protocol
                    if hasattr(protocol, 'key_event'):
                        protocol.key_event(key_code, key_down)
            except Exception as e:
                print(f"Error sending key: {e}")

    def send_mouse_event(self, x, y, button_mask=0):
        """Send a mouse event to the VNC server."""
        if self.vnc_client and self.connected:
            try:
                # Send mouse event to VNC server
                if hasattr(self.vnc_client.screen, 'protocol'):
                    protocol = self.vnc_client.screen.protocol
                    if hasattr(protocol, 'pointer_event'):
                        protocol.pointer_event(x, y, button_mask)
            except Exception as e:
                print(f"Error sending mouse event: {e}")

    def pygame_key_to_vnc_key(self, pygame_key):
        """Convert Pygame key code to VNC key code."""
        # Basic key mapping - this may need expansion
        key_map = {
            pygame.K_BACKSPACE: 0xFF08,
            pygame.K_TAB: 0xFF09,
            pygame.K_RETURN: 0xFF0D,
            pygame.K_ESCAPE: 0xFF1B,
            pygame.K_SPACE: 0x0020,
            pygame.K_DELETE: 0xFFFF,
            pygame.K_LEFT: 0xFF51,
            pygame.K_UP: 0xFF52,
            pygame.K_RIGHT: 0xFF53,
            pygame.K_DOWN: 0xFF54,
            pygame.K_F1: 0xFFBE,
            pygame.K_F2: 0xFFBF,
            pygame.K_F3: 0xFFC0,
            pygame.K_F4: 0xFFC1,
            pygame.K_F5: 0xFFC2,
            pygame.K_F6: 0xFFC3,
            pygame.K_F7: 0xFFC4,
            pygame.K_F8: 0xFFC5,
            pygame.K_F9: 0xFFC6,
            pygame.K_F10: 0xFFC7,
            pygame.K_F11: 0xFFC8,
            pygame.K_F12: 0xFFC9,
            pygame.K_LSHIFT: 0xFFE1,
            pygame.K_RSHIFT: 0xFFE2,
            pygame.K_LCTRL: 0xFFE3,
            pygame.K_RCTRL: 0xFFE4,
            pygame.K_LALT: 0xFFE9,
            pygame.K_RALT: 0xFFEA,
        }

        # Return mapped key or the pygame key itself for printable characters
        return key_map.get(pygame_key, pygame_key)

    def pygame_mouse_to_vnc_button(self, pygame_button):
        """Convert Pygame mouse button to VNC button mask."""
        button_map = {
            1: 0x01,  # Left button
            2: 0x02,  # Middle button
            3: 0x04,  # Right button
            4: 0x08,  # Wheel up
            5: 0x10,  # Wheel down
        }
        return button_map.get(pygame_button, 0)
