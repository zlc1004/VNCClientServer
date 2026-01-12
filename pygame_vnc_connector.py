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

            # Create VNC client configuration
            self.vnc_client = Client(
                host=host,
                port=int(port),
                password=password,
                depth=32,
                fast=True,
                shared=True,
                gui=False,
                array=True  # Enable array mode for easier screen capture
            )

            # Start connection in a non-blocking way
            self.connection_thread = Thread(target=self._run_vnc_client_nonblocking, daemon=True)
            self.connection_thread.start()

            # Wait for connection with timeout
            timeout = 10  # 10 second timeout
            start_time = time.time()

            while time.time() - start_time < timeout:
                if self._check_connection_status():
                    print("VNC connection established successfully")
                    return True
                time.sleep(0.5)

            print("VNC connection timed out")
            return False

        except Exception as e:
            print(f"Approach 1 failed: {e}")

        # Approach 2: Try with a simpler configuration
        try:
            print("Trying VNC with simplified configuration...")

            self.vnc_client = Client(
                host=host,
                port=int(port),
                password=password,
                depth=16,  # Use lower depth for better performance
                fast=True,
                shared=True,
                gui=False,
                array=True
            )

            self.connection_thread = Thread(target=self._run_vnc_client_nonblocking, daemon=True)
            self.connection_thread.start()

            # Wait for connection with timeout
            timeout = 10
            start_time = time.time()

            while time.time() - start_time < timeout:
                if self._check_connection_status():
                    print("VNC connection established successfully")
                    return True
                time.sleep(0.5)

            print("VNC connection timed out")
            return False

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

    def _run_vnc_client_nonblocking(self):
        """Run the VNC client in a non-blocking way."""
        try:
            if self.vnc_client:
                print("Starting VNC client in non-blocking mode...")

                # Set up connection success callback
                self.vnc_client._on_connect_success = self._on_vnc_connect_success
                self.vnc_client._on_connect_failure = self._on_vnc_connect_failure

                # Try to start the client without blocking
                # Use a custom reactor loop approach
                self._start_vnc_with_timeout()

        except Exception as e:
            print(f"Error in VNC client thread: {e}")
            self.connected = False

    def _start_vnc_with_timeout(self):
        """Start VNC client with proper timeout handling."""
        try:
            # Set up connection monitoring
            self.connection_attempts = 0
            self.max_attempts = 30  # 30 attempts with 0.5 second intervals = 15 seconds max

            # Start the actual VNC connection attempt
            if hasattr(self.vnc_client, 'start'):
                # Run in a way that doesn't block the entire application
                self._monitor_vnc_startup()
            else:
                print("VNC client doesn't have start method")
                self.connected = False

        except Exception as e:
            print(f"Error starting VNC with timeout: {e}")
            self.connected = False

    def _monitor_vnc_startup(self):
        """Monitor VNC startup without blocking."""
        try:
            print("Monitoring VNC startup...")

            # Try to establish connection
            connection_established = False

            while self.connection_attempts < self.max_attempts and not connection_established:
                try:
                    # Attempt connection
                    if not hasattr(self, '_connection_started'):
                        self.vnc_client.start()
                        self._connection_started = True

                    # Check if connection is established
                    if self._check_connection_status():
                        connection_established = True
                        self.connected = True
                        print("VNC connection successful!")
                        self._start_screen_monitoring()
                        break

                    time.sleep(0.5)
                    self.connection_attempts += 1

                except Exception as e:
                    print(f"Connection attempt {self.connection_attempts} failed: {e}")
                    self.connection_attempts += 1
                    time.sleep(0.5)

            if not connection_established:
                print("VNC connection failed after all attempts")
                self.connected = False

        except Exception as e:
            print(f"Error in VNC startup monitoring: {e}")
            self.connected = False

    def _check_connection_status(self):
        """Check if VNC connection is properly established."""
        try:
            if not self.vnc_client:
                return False

            # Check various indicators that connection is established
            if hasattr(self.vnc_client, 'screen') and self.vnc_client.screen is not None:
                return True

            if hasattr(self.vnc_client, 'connected') and self.vnc_client.connected:
                return True

            if hasattr(self.vnc_client, '_connected') and self.vnc_client._connected:
                return True

            return False

        except Exception as e:
            print(f"Error checking connection status: {e}")
            return False

    def _on_vnc_connect_success(self):
        """Callback for successful VNC connection."""
        print("VNC connection success callback triggered")
        self.connected = True
        self._start_screen_monitoring()

    def _on_vnc_connect_failure(self, error):
        """Callback for failed VNC connection."""
        print(f"VNC connection failure callback triggered: {error}")
        self.connected = False

    def _start_screen_monitoring(self):
        """Start monitoring screen updates after successful connection."""
        print("Starting screen monitoring...")
        try:
            # Start screen capture in a separate thread
            self.screen_monitor_thread = Thread(target=self._screen_monitor_loop, daemon=True)
            self.screen_monitor_thread.start()
        except Exception as e:
            print(f"Error starting screen monitoring: {e}")

    def _screen_monitor_loop(self):
        """Monitor screen updates without blocking."""
        print("Screen monitoring loop started")

        while self.connected and self.vnc_client:
            try:
                # Capture screen at reasonable intervals
                time.sleep(0.1)  # ~10 FPS
                self._capture_screen()

            except Exception as e:
                print(f"Error in screen monitoring loop: {e}")
                # Don't break on single errors, just log them
                time.sleep(1)  # Wait a bit longer on error

        print("Screen monitoring loop ended")

    def _capture_screen(self):
        """Capture current screen from VNC client."""
        try:
            if not self.vnc_client or not self.connected:
                return

            # Try multiple approaches to get screen data
            screen_data = None

            # Approach 1: Direct screen attribute
            if hasattr(self.vnc_client, 'screen') and self.vnc_client.screen is not None:
                screen = self.vnc_client.screen

                # Try to get image data
                if hasattr(screen, 'save'):
                    try:
                        import io
                        buffer = io.BytesIO()
                        screen.save(buffer, format='PNG')
                        buffer.seek(0)

                        # Load as PIL image
                        pil_image = Image.open(buffer)
                        screen_data = pil_image

                    except Exception as e:
                        # Try different format
                        pass

                elif hasattr(screen, 'image') and screen.image is not None:
                    screen_data = screen.image

                elif hasattr(screen, 'data'):
                    # Raw screen data
                    try:
                        # Convert raw data to PIL image
                        if hasattr(screen, 'width') and hasattr(screen, 'height'):
                            width = screen.width
                            height = screen.height
                            # Assume RGB format
                            screen_data = Image.frombytes('RGB', (width, height), screen.data)
                    except Exception as e:
                        pass

            # Approach 2: Check if client has direct image access
            elif hasattr(self.vnc_client, 'image') and self.vnc_client.image is not None:
                screen_data = self.vnc_client.image

            # Convert to Pygame surface if we got screen data
            if screen_data:
                self._convert_to_pygame_surface(screen_data)

        except Exception as e:
            # Only log actual errors, not "no screen data yet" situations
            if "No screen data" not in str(e):
                print(f"Screen capture error: {e}")

    def _convert_to_pygame_surface(self, pil_image):
        """Convert PIL image to Pygame surface."""
        try:
            # Ensure PIL image is in RGB mode
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Convert to Pygame surface
            mode = pil_image.mode
            size = pil_image.size
            data = pil_image.tobytes()

            with self.screen_lock:
                self.pygame_surface = pygame.image.fromstring(data, size, mode)

        except Exception as e:
            print(f"Error converting to Pygame surface: {e}")

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
        """Disconnect from VNC server with comprehensive cleanup."""
        print("Disconnecting from VNC...")

        # Set disconnected state immediately to stop all threads
        self.connected = False

        # Clean up VNC client
        if self.vnc_client:
            try:
                # Try multiple disconnection approaches
                if hasattr(self.vnc_client, 'stop'):
                    print("Stopping VNC client...")
                    self.vnc_client.stop()

                if hasattr(self.vnc_client, 'disconnect'):
                    print("Calling VNC disconnect...")
                    self.vnc_client.disconnect()

                if hasattr(self.vnc_client, 'screen') and self.vnc_client.screen:
                    screen = self.vnc_client.screen
                    if hasattr(screen, 'protocol') and screen.protocol:
                        if hasattr(screen.protocol, 'transport') and screen.protocol.transport:
                            print("Closing VNC transport...")
                            screen.protocol.transport.loseConnection()

            except Exception as e:
                print(f"Error during VNC client cleanup: {e}")

        # Wait for connection thread to finish
        if hasattr(self, 'connection_thread') and self.connection_thread:
            try:
                if self.connection_thread.is_alive():
                    print("Waiting for connection thread to finish...")
                    self.connection_thread.join(timeout=5)  # 5 second timeout
            except Exception as e:
                print(f"Error waiting for connection thread: {e}")

        # Wait for screen monitor thread to finish
        if hasattr(self, 'screen_monitor_thread') and self.screen_monitor_thread:
            try:
                if self.screen_monitor_thread.is_alive():
                    print("Waiting for screen monitor thread to finish...")
                    self.screen_monitor_thread.join(timeout=2)  # 2 second timeout
            except Exception as e:
                print(f"Error waiting for screen monitor thread: {e}")

        # Clean up resources
        self.vnc_client = None
        with self.screen_lock:
            self.pygame_surface = None

        print("VNC disconnection complete")

    def is_connected(self):
        """Check if VNC client is connected with thorough verification."""
        try:
            if not self.connected or self.vnc_client is None:
                return False

            # Check if connection thread is still alive
            if hasattr(self, 'connection_thread') and self.connection_thread:
                if not self.connection_thread.is_alive():
                    # Connection thread died, assume disconnected
                    self.connected = False
                    return False

            # Additional checks for VNC client state
            return self._check_connection_status()

        except Exception as e:
            print(f"Error checking connection: {e}")
            self.connected = False
            return False

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
