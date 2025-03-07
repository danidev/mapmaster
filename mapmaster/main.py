"""
MapMaster - A local battlemap tool for tabletop RPGs.
Main application entry point.
"""

import os
import sys
import pygame
from pygame.locals import *
import argparse
import threading
import time

from .config import Config
from .utils.network import get_local_ip, find_free_port
from .ui.overlay import OverlayManager
from .battle.map import MapManager
from .battle.token import TokenManager
from .server.app import create_app, start_server

# Default colors for annotations
DEFAULT_COLORS = {
    "Red": (255, 0, 0),
    "Blue": (0, 0, 255),
    "Green": (0, 255, 0),
    "Yellow": (255, 255, 0),
    "White": (255, 255, 255),
    "Black": (0, 0, 0)
}

# Default brush sizes
DEFAULT_BRUSH_SIZES = {
    "Tiny": 2,
    "Small": 5,
    "Medium": 10,
    "Large": 15,
    "Huge": 25
}

# Command overlay text
DEFAULT_COMMANDS = [
    "== MapMaster Controls ==",
    "",
    "F1: Show/hide this help overlay",
    "F3: Show/hide tokens",
    "F4: Show/hide map name",
    "G: Toggle grid overlay",
    "F11: Toggle fullscreen",
    "",
    "Left/Right arrows: Change map",
    "Space: Next map",
    "P: Pause/resume streaming",
    "ESC: Exit",
    "",
    "== Mouse Controls ==",
    "Left-click on empty space: Add a new token",
    "Left-click on token: Select and drag token",
    "Right-click: Deselect token",
    "",
    "== Network ==",
    f"Connect from mobile devices at: http://<SERVER_IP>:<PORT>"
]

class MapMasterApp:
    """Main application class for MapMaster."""
    
    def __init__(self):
        """Initialize the application."""
        # Parse command line arguments
        parser = argparse.ArgumentParser(description="MapMaster - A local battlemap tool for tabletop RPGs")
        parser.add_argument('--fullscreen', action='store_true', help='Start in fullscreen mode')
        parser.add_argument('--port', type=int, default=0, help='Port for the web server (0 for auto)')
        parser.add_argument('--no-server', action='store_true', help='Disable the web server')
        parser.add_argument('--maps', type=str, default=None, help='Custom maps directory')
        args = parser.parse_args()
        
        # Load configuration
        self.config = Config()
        
        # Override config with command line arguments
        if args.fullscreen:
            self.config.set("fullscreen", True)
        if args.maps:
            self.config.set("maps_directory", args.maps)
            
        # Initialize Pygame
        pygame.init()
        pygame.display.set_caption("MapMaster")
        
        # Set up display
        self.setup_display()
        
        # Initialize components
        self.overlay_manager = OverlayManager(self.screen)
        self.overlay_manager.set_help_text(DEFAULT_COMMANDS)
        self.overlay_manager.set_colors(DEFAULT_COLORS)
        self.overlay_manager.set_brush_sizes(DEFAULT_BRUSH_SIZES)
        
        self.map_manager = MapManager(self.screen, self.config)
        self.token_manager = TokenManager(self.screen, self.config)

        # Connect token manager to overlay manager
        self.overlay_manager.token_manager = self.token_manager
        
        # State tracking
        self.running = False
        self.dragging_token = False
        self.pause_streaming = False
        
        # Server setup
        self.server_enabled = not args.no_server
        self.server_thread = None
        self.server_app = None
        
        if self.server_enabled:
            # Find a port to use
            port = args.port if args.port else find_free_port(5000)
            self.config.set("port", port)
            
            # Create Flask app
            self.server_app = create_app(self)
            
            # Start server in a thread
            self.server_thread = threading.Thread(
                target=start_server,
                args=(self.server_app, get_local_ip(), port),
                daemon=True
            )
            
            # Update help text with server information
            ip = get_local_ip()
            commands = self.overlay_manager.help_text.copy()
            for i, line in enumerate(commands):
                if "<SERVER_IP>:<PORT>" in line:
                    commands[i] = f"Connect from mobile devices at: http://{ip}:{port}"
                    break
            self.overlay_manager.set_help_text(commands)
            
            # Show initial notification
            self.overlay_manager.add_notification(f"Server running at http://{ip}:{port}", 10.0)
        
        # Create a sample token if no token images found
        if not self.token_manager.available_tokens:
            # Create a sample directory
            os.makedirs(self.config.get("tokens_directory", "assets/tokens"), exist_ok=True)
            
            # Create a simple circular token image
            token_size = 50
            sample_surface = pygame.Surface((token_size, token_size), pygame.SRCALPHA)
            sample_surface.fill((0, 0, 0, 0))  # Transparent background
            
            # Draw a filled circle
            pygame.draw.circle(sample_surface, (255, 0, 0), (token_size//2, token_size//2), token_size//2)
            
            # Add some contrast with an inner circle
            pygame.draw.circle(sample_surface, (200, 0, 0), (token_size//2, token_size//2), token_size//3)
            
            # Save it
            sample_path = os.path.join(self.config.get("tokens_directory", "assets/tokens"), "sample_token.png")
            pygame.image.save(sample_surface, sample_path)
            
            # Refresh token list
            self.token_manager.refresh_token_list()
    
    def setup_display(self):
        """Set up the display according to configuration."""
        fullscreen = self.config.get("fullscreen", False)
        width = self.config.get("window_width", 1280)
        height = self.config.get("window_height", 720)
        
        if fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        
        # Save actual dimensions back to config
        screen_rect = self.screen.get_rect()
        self.config.set("window_width", screen_rect.width)
        self.config.set("window_height", screen_rect.height)
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        fullscreen = not self.config.get("fullscreen", False)
        self.config.set("fullscreen", fullscreen)
        
        # Remember current dimensions before switching
        current_rect = self.screen.get_rect()
        
        # Switch mode
        pygame.display.quit()
        pygame.display.init()
        self.setup_display()
        
        # Reinitialize components that depend on screen
        self.overlay_manager.screen = self.screen
        
        return fullscreen
    
    def handle_events(self):
        """Process events from the event queue."""
        for event in pygame.event.get():
            # Exit events
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Keyboard events
            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
                
            # Mouse button press
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.overlay_manager.handle_click(event.pos):
                    continue  # Click handled by overlay
                
                if event.button == 1:  # Left click
                    self.handle_left_mousedown(event.pos)
                elif event.button == 3:  # Right click
                    self.handle_right_mousedown(event.pos)
                elif event.button == 2:  # Middle click
                    self.handle_middle_mousedown(event.pos)
            
            # Mouse button release
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    if self.dragging_token:
                        self.dragging_token = False
                        if self.token_manager.selected_token:
                            self.token_manager.selected_token.end_drag()
                elif event.button == 3:  # Right click
                    # Clear token selection
                    if self.token_manager.selected_token:
                        self.token_manager.selected_token.selected = False
                        self.token_manager.selected_token = None
            
            # Mouse motion
            if event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
            
            # Window resize
            if event.type == pygame.VIDEORESIZE:
                if not self.config.get("fullscreen", False):
                    self.config.set("window_width", event.w)
                    self.config.set("window_height", event.h)
    
    def handle_keydown(self, event):
        """Handle keyboard key presses."""
        if event.key == pygame.K_ESCAPE:
            self.running = False
        
        # Function keys
        elif event.key == pygame.K_F1:
            self.overlay_manager.toggle_help()
        elif event.key == pygame.K_F3:
            self.token_manager.tokens_visible = not self.token_manager.tokens_visible
            self.overlay_manager.add_notification(
                f"Tokens {'visible' if self.token_manager.tokens_visible else 'hidden'}"
            )
        elif event.key == pygame.K_F4:
            self.overlay_manager.toggle_filename()
        elif event.key == pygame.K_F11:
            fullscreen = self.toggle_fullscreen()
            self.overlay_manager.add_notification(
                f"{'Fullscreen mode' if fullscreen else 'Windowed mode'}"
            )
        
        # Navigation keys
        elif event.key in (pygame.K_RIGHT, pygame.K_SPACE):
            if self.map_manager.next_map():
                self.overlay_manager.add_notification("Next map loaded")
        elif event.key == pygame.K_LEFT:
            if self.map_manager.previous_map():
                self.overlay_manager.add_notification("Previous map loaded")
        
        # Toggle grid
        elif event.key == pygame.K_g:
            grid_enabled = self.map_manager.toggle_grid()
            self.overlay_manager.add_notification(
                f"Grid {'enabled' if grid_enabled else 'disabled'}"
            )
        
        # Toggle streaming pause
        elif event.key == pygame.K_p:
            self.pause_streaming = not self.pause_streaming
            self.overlay_manager.add_notification(
                f"Streaming {'paused' if self.pause_streaming else 'resumed'}"
            )
        
        # Delete selected token
        elif event.key == pygame.K_BACKSPACE:
            if self.token_manager.selected_token:
                token_name = self.token_manager.selected_token.name
                self.token_manager.remove_token(self.token_manager.selected_token)
                self.overlay_manager.add_notification(f"Deleted token: {token_name}")
        
    def handle_left_mousedown(self, pos):
        """Handle left mouse button press for token selection and movement."""
        # Check if we clicked on an existing token
        for token in self.token_manager.tokens:
            if token.contains_point(pos):
                # Select this token
                self.token_manager.selected_token = token
                token.selected = True
                token.start_drag(pos)
                self.dragging_token = True
                
                # Deselect all other tokens
                for other in self.token_manager.tokens:
                    if other != token:
                        other.selected = False
                return
        
        # If no token was clicked, show token selector to place a new token
        if self.token_manager.available_tokens:
            self.overlay_manager.show_token_selector = True
            self.overlay_manager.token_click_pos = pos  # Store position for placement
        else:
            self.overlay_manager.add_notification("No token images found", 3.0)
    
    def handle_right_mousedown(self, pos):
        """Handle right mouse button press."""
        # Select or drag tokens
        for token in self.token_manager.tokens:
            if token.contains_point(pos):
                # Select this token
                self.token_manager.selected_token = token
                token.selected = True
                token.start_drag(pos)
                self.dragging_token = True
                
                # Deselect all other tokens
                for other in self.token_manager.tokens:
                    if other != token:
                        other.selected = False
                
                self.overlay_manager.add_notification(f"Selected {token.name}")
                return
        
        # If no token was clicked, deselect all
        self.token_manager.selected_token = None
        for token in self.token_manager.tokens:
            token.selected = False
    
    def handle_middle_mousedown(self, pos):
        """Handle middle mouse button press (add token)."""
        if not self.token_manager.available_tokens:
            self.overlay_manager.add_notification("No token images found", 3.0)
            return
        
        # Toggle token selector
        self.overlay_manager.toggle_token_selector()
    
    def handle_mouse_motion(self, pos):
        """Handle mouse movement."""
        if self.dragging_token and self.token_manager.selected_token:
            # Move the selected token
            self.token_manager.selected_token.update_drag(pos)
    
    def update(self):
        """Update game state."""
        # Nothing to update here for now
        pass
    
    def draw(self):
        """Draw all components to the screen."""
        # Start with a clean slate
        self.screen.fill((0, 0, 0))  # Black background
        
        # Draw the map
        self.map_manager.draw_map_only()
        
        # Draw grid if enabled (BEFORE tokens)
        if self.map_manager.grid_enabled:
            self.map_manager.draw_grid()
        
        # Draw tokens if visible
        if self.token_manager.tokens_visible:
            self.token_manager.draw()
        
        # Draw UI overlays
        self.overlay_manager.draw(current_filename=self.map_manager.get_current_filename())
        
        # Flip the display
        pygame.display.flip()
    
    def run(self):
        """Run the main application loop."""
        self.running = True
        
        # Start server if enabled
        if self.server_enabled and self.server_thread:
            self.server_thread.start()
        
        # Main loop
        clock = pygame.time.Clock()
        while self.running:
            # Process events
            self.handle_events()
            
            # Update game state
            self.update()
            
            # Draw everything
            self.draw()
            
            # Cap the frame rate
            clock.tick(60)
        
        # Clean up
        pygame.quit()
        
        # Update config with final settings
        self.config.save()
        
        print("MapMaster closed. Thank you for using MapMaster!")
    
    def get_screen_image(self):
        """Get the current screen image for streaming."""
        if self.pause_streaming:
            # Return a paused indicator image
            surface = pygame.Surface(self.screen.get_size())
            surface.fill((40, 40, 40))  # Dark gray
            
            font = pygame.font.SysFont('Arial', 36)
            text = font.render("Streaming Paused", True, (255, 255, 255))
            text_rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
            surface.blit(text, text_rect)
            
            return surface
        
        return self.screen


def main():
    """Entry point for the application."""
    app = MapMasterApp()
    app.run()


if __name__ == "__main__":
    main()