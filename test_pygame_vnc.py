#!/usr/bin/env python3
"""
Simple test script to verify Pygame VNC setup
"""

import pygame
import sys
import time

def test_pygame_setup():
    """Test basic Pygame functionality."""
    print("Testing Pygame setup...")
    
    try:
        pygame.init()
        
        # Get display info
        info = pygame.display.Info()
        print(f"Screen resolution: {info.current_w}x{info.current_h}")
        
        # Create a small test window
        screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Pygame VNC Test")
        
        # Colors
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        GREEN = (0, 255, 0)
        
        # Font
        font = pygame.font.Font(None, 36)
        
        # Main loop
        clock = pygame.time.Clock()
        running = True
        
        print("Pygame test window opened. Press ESC to close.")
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            # Clear screen
            screen.fill(BLACK)
            
            # Draw test text
            text = font.render("Pygame VNC Test - Press ESC to exit", True, WHITE)
            text_rect = text.get_rect(center=(400, 300))
            screen.blit(text, text_rect)
            
            # Draw a simple animation
            time_ms = pygame.time.get_ticks()
            x = 400 + int(100 * pygame.math.cos(time_ms / 1000.0))
            pygame.draw.circle(screen, GREEN, (x, 400), 20)
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        print("Pygame test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Pygame test failed: {e}")
        return False

def test_vnc_imports():
    """Test VNC-related imports."""
    print("Testing VNC imports...")
    
    try:
        from pygame_vnc_connector import PygameVNCConnector
        print("✓ PygameVNCConnector import successful")
        
        connector = PygameVNCConnector()
        print("✓ PygameVNCConnector instantiation successful")
        
        try:
            from pyVNC.Client import Client
            print("✓ pyVNC Client import successful")
        except ImportError as e:
            print(f"⚠ pyVNC import issue: {e}")
            
        return True
        
    except Exception as e:
        print(f"VNC import test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Pygame VNC Test Suite ===")
    print()
    
    # Test imports first
    import_success = test_vnc_imports()
    print()
    
    # Test pygame if imports worked
    if import_success:
        pygame_success = test_pygame_setup()
        
        if pygame_success:
            print("✅ All tests passed! Pygame VNC setup is ready.")
        else:
            print("❌ Pygame test failed.")
    else:
        print("❌ Import tests failed. Check dependencies.")
