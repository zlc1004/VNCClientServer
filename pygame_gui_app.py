"""
Pygame-based GUI Application for VNC QR Server
Displays QR code initially, then allows pyVNC to take over the window
"""

import pygame
import sys
import os
from threading import Thread
import time
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import socket

from pygame_vnc_connector import PygameVNCConnector
from gui_vnc_handler import VNCHandler
from network_utils import get_local_ip

class PygameVNCQRApp:
    def __init__(self, config_manager, web_server):
        self.config_manager = config_manager
        self.web_server = web_server

        # Initialize Pygame
        pygame.init()

        # Get screen info and create fullscreen window
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h

        # Create fullscreen display
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("VNC QR Server")

        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.BLUE = (52, 152, 219)
        self.GREEN = (39, 174, 96)
        self.RED = (231, 76, 60)

        # Fonts
        try:
            self.title_font = pygame.font.Font(None, 48)
            self.subtitle_font = pygame.font.Font(None, 32)
            self.text_font = pygame.font.Font(None, 24)
        except:
            self.title_font = pygame.font.SysFont('Arial', 48)
            self.subtitle_font = pygame.font.SysFont('Arial', 32)
            self.text_font = pygame.font.SysFont('Arial', 24)

        # State
        self.vnc_mode = False
        self.running = True
        self.qr_image = None
        self.status_text = "Ready to connect"

        # VNC components
        self.vnc_connector = PygameVNCConnector()
        self.vnc_handler = VNCHandler(self)

        # Set up web server callback
        self.web_server.set_vnc_callback(self.vnc_handler.handle_vnc_request)

        # Generate QR code
        self.generate_qr_code()

        # Clock for FPS control
        self.clock = pygame.time.Clock()

    def generate_qr_code(self):
        """Generate QR code for mobile access."""
        try:
            local_ip = get_local_ip()
            qr_url = f"http://{local_ip}:8080"

            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)

            # Create PIL image
            pil_img = qr.make_image(fill_color="black", back_color="white")

            # Resize QR code to fit screen nicely
            qr_size = min(self.screen_width, self.screen_height) // 2
            try:
                # Try newer PIL versions first
                pil_img = pil_img.resize((qr_size, qr_size), Image.Resampling.NEAREST)
            except AttributeError:
                # Fallback for older PIL versions
                pil_img = pil_img.resize((qr_size, qr_size), Image.NEAREST)

            # Convert PIL image to RGB mode to ensure compatibility
            if pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')

            # Convert PIL image to Pygame surface
            mode = pil_img.mode
            size = pil_img.size
            data = pil_img.tobytes()

            self.qr_image = pygame.image.fromstring(data, size, mode)
            self.qr_url = qr_url

        except Exception as e:
            print(f"Error generating QR code: {e}")
            self.qr_image = None
            self.qr_url = "Error generating QR code"

    def draw_qr_mode(self):
        """Draw the QR code interface."""
        # Clear screen with white background
        self.screen.fill(self.WHITE)

        # Calculate positions
        center_x = self.screen_width // 2
        center_y = self.screen_height // 2

        # Draw title in black
        title_text = self.title_font.render("VNC QR Server", True, self.BLACK)
        title_rect = title_text.get_rect(center=(center_x, 80))
        self.screen.blit(title_text, title_rect)

        # Draw QR code if available
        if self.qr_image:
            qr_rect = self.qr_image.get_rect(center=(center_x, center_y - 50))
            self.screen.blit(self.qr_image, qr_rect)
        else:
            # If QR code generation failed, show error message
            error_text = self.subtitle_font.render("QR Code Generation Failed", True, self.RED)
            error_rect = error_text.get_rect(center=(center_x, center_y - 50))
            self.screen.blit(error_text, error_rect)

            # Draw a placeholder rectangle
            placeholder_rect = pygame.Rect(center_x - 150, center_y - 150, 300, 300)
            pygame.draw.rect(self.screen, self.RED, placeholder_rect, 3)

        # Draw URL text in blue
        url_text = self.subtitle_font.render(f"Scan QR code or visit:", True, self.BLUE)
        url_rect = url_text.get_rect(center=(center_x, center_y + 200))
        self.screen.blit(url_text, url_rect)

        url_value = self.subtitle_font.render(self.qr_url, True, self.BLACK)
        url_value_rect = url_value.get_rect(center=(center_x, center_y + 240))
        self.screen.blit(url_value, url_value_rect)

        # Draw status
        status_color = self.GREEN if "connected" in self.status_text.lower() else self.BLACK
        status = self.text_font.render(f"Status: {self.status_text}", True, status_color)
        status_rect = status.get_rect(center=(center_x, self.screen_height - 100))
        self.screen.blit(status, status_rect)

        # Draw instructions in black
        instructions = [
            "1. Scan QR code with mobile device",
            "2. Enter VNC server details in web interface",
            "3. Connect to start VNC session",
            "Press ESC to exit"
        ]

        y_offset = self.screen_height - 200
        for i, instruction in enumerate(instructions):
            text = self.text_font.render(instruction, True, self.BLACK)
            text_rect = text.get_rect(center=(center_x, y_offset + i * 30))
            self.screen.blit(text, text_rect)

    def draw_vnc_mode(self):
        """Draw the VNC connection interface."""
        # Clear screen
        self.screen.fill(self.BLACK)

        # Get VNC screen surface
        vnc_surface = self.vnc_connector.get_screen_surface()

        if vnc_surface:
            # Scale VNC screen to fit our window while maintaining aspect ratio
            vnc_rect = vnc_surface.get_rect()
            screen_rect = self.screen.get_rect()

            # Calculate scaling to fit screen
            scale_x = screen_rect.width / vnc_rect.width
            scale_y = screen_rect.height / vnc_rect.height
            scale = min(scale_x, scale_y)

            # Scale the surface
            new_width = int(vnc_rect.width * scale)
            new_height = int(vnc_rect.height * scale)
            scaled_surface = pygame.transform.scale(vnc_surface, (new_width, new_height))

            # Center the scaled surface
            scaled_rect = scaled_surface.get_rect(center=screen_rect.center)

            # Draw the VNC screen
            self.screen.blit(scaled_surface, scaled_rect)

            # Store the VNC display area for mouse coordinate translation
            self.vnc_display_rect = scaled_rect
            self.vnc_scale = scale

        else:
            # No VNC screen available yet, show placeholder with white background
            self.screen.fill(self.WHITE)
            center_x = self.screen_width // 2
            center_y = self.screen_height // 2

            # Draw VNC status
            title_text = self.title_font.render("VNC Connected", True, self.GREEN)
            title_rect = title_text.get_rect(center=(center_x, center_y - 50))
            self.screen.blit(title_text, title_rect)

            # Draw instructions in black
            instruction1 = self.subtitle_font.render("Waiting for screen data...", True, self.BLACK)
            instruction1_rect = instruction1.get_rect(center=(center_x, center_y + 20))
            self.screen.blit(instruction1, instruction1_rect)

            instruction2 = self.text_font.render("Press ESC to disconnect", True, self.BLACK)
            instruction2_rect = instruction2.get_rect(center=(center_x, center_y + 60))
            self.screen.blit(instruction2, instruction2_rect)

            # Draw status at bottom
            status = self.text_font.render(f"Status: {self.status_text}", True, self.GREEN)
            status_rect = status.get_rect(center=(center_x, self.screen_height - 30))
            self.screen.blit(status, status_rect)

    def switch_to_vnc_mode(self):
        """Switch to VNC mode - let pyVNC take over the window."""
        print("Switching to VNC mode")
        self.vnc_mode = True
        self.status_text = "VNC Connected"

        # Configure pyVNC to use our Pygame window
        # This is where we'll let pyVNC take over
        self.setup_vnc_takeover()

    def setup_vnc_takeover(self):
        """Configure pyVNC to use our Pygame window."""
        try:
            # Start monitoring for VNC screen updates
            self.vnc_update_thread = Thread(target=self._monitor_vnc_updates, daemon=True)
            self.vnc_update_thread.start()

        except Exception as e:
            print(f"Error setting up VNC takeover: {e}")

    def _monitor_vnc_updates(self):
        """Monitor VNC for screen updates."""
        print("Starting VNC screen monitoring...")
        while self.vnc_mode and self.vnc_connector.is_connected():
            try:
                time.sleep(0.1)  # Check for updates 10 times per second
                # The screen will be updated in the main draw loop
            except Exception as e:
                print(f"Error in VNC monitoring: {e}")
                break

    def switch_to_qr_mode(self):
        """Switch back to QR code mode."""
        print("Switching to QR mode")
        self.vnc_mode = False
        self.status_text = "Ready to connect"

        # Disconnect VNC
        self.vnc_handler.disconnect_vnc()

    def update_status(self, message):
        """Update status message."""
        self.status_text = message
        print(f"Status: {message}")

    def handle_events(self):
        """Handle Pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.vnc_mode:
                        self.switch_to_qr_mode()
                    else:
                        self.running = False

                # Pass other keys to VNC if in VNC mode
                elif self.vnc_mode and self.vnc_connector.is_connected():
                    # Convert pygame key to VNC key and send
                    self.send_key_to_vnc(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.vnc_mode and self.vnc_connector.is_connected():
                    # Send mouse click to VNC
                    x, y = event.pos
                    button = event.button
                    self.send_mouse_to_vnc(x, y, button)

            elif event.type == pygame.MOUSEBUTTONUP:
                if self.vnc_mode and self.vnc_connector.is_connected():
                    # Send mouse release to VNC
                    x, y = event.pos
                    # Send mouse up event (button mask 0)
                    if hasattr(self, 'vnc_display_rect') and hasattr(self, 'vnc_scale'):
                        vnc_x = int((x - self.vnc_display_rect.x) / self.vnc_scale)
                        vnc_y = int((y - self.vnc_display_rect.y) / self.vnc_scale)
                        self.vnc_connector.send_mouse_event(vnc_x, vnc_y, 0)

            elif event.type == pygame.MOUSEMOTION:
                if self.vnc_mode and self.vnc_connector.is_connected():
                    # Send mouse movement to VNC
                    x, y = event.pos
                    if hasattr(self, 'vnc_display_rect') and hasattr(self, 'vnc_scale'):
                        vnc_x = int((x - self.vnc_display_rect.x) / self.vnc_scale)
                        vnc_y = int((y - self.vnc_display_rect.y) / self.vnc_scale)
                        self.vnc_connector.send_mouse_event(vnc_x, vnc_y, 0)

    def send_key_to_vnc(self, pygame_key):
        """Convert Pygame key to VNC key and send."""
        try:
            # Convert pygame key to VNC key format
            vnc_key = self.vnc_connector.pygame_key_to_vnc_key(pygame_key)
            self.vnc_connector.send_key_event(vnc_key, True)  # Key down
            self.vnc_connector.send_key_event(vnc_key, False)  # Key up
        except Exception as e:
            print(f"Error sending key to VNC: {e}")

    def send_mouse_to_vnc(self, x, y, button):
        """Send mouse event to VNC."""
        try:
            if hasattr(self, 'vnc_display_rect') and hasattr(self, 'vnc_scale'):
                # Translate mouse coordinates from screen to VNC coordinates
                vnc_x = int((x - self.vnc_display_rect.x) / self.vnc_scale)
                vnc_y = int((y - self.vnc_display_rect.y) / self.vnc_scale)

                # Convert pygame button to VNC button mask
                button_mask = self.vnc_connector.pygame_mouse_to_vnc_button(button)

                # Send mouse event
                self.vnc_connector.send_mouse_event(vnc_x, vnc_y, button_mask)
        except Exception as e:
            print(f"Error sending mouse to VNC: {e}")

    def run(self):
        """Main application loop."""
        print("Starting Pygame VNC QR Server...")

        while self.running:
            # Handle events
            self.handle_events()

            # Draw current mode
            if self.vnc_mode:
                self.draw_vnc_mode()
            else:
                self.draw_qr_mode()

            # Update display
            pygame.display.flip()

            # Control frame rate
            self.clock.tick(60)

        # Cleanup
        self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        try:
            if self.vnc_connector:
                self.vnc_connector.disconnect()
        except Exception as e:
            print(f"Error during cleanup: {e}")

        pygame.quit()
        sys.exit()
