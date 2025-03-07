"""
Token management module for MapMaster.
Handles character and monster tokens on the battlefield.
"""

import os
import pygame
import json
from ..utils.image import load_image, get_image_files

class Token:
    """
    Represents a single token on the map (character, monster, etc.)
    """
    
    def __init__(self, image_path, position, size=50, name="Token"):
        """Initialize a token."""
        self.original_image = load_image(image_path)
        self.image_path = image_path
        self.position = position  # Center position
        self.size = size
        self.name = name
        self.selected = False
        self.visible = True
        self.dragging = False
        self.drag_offset = (0, 0)
        
        # Process image
        self.update_image()
    
    def update_image(self):
        """Update the token image with current size."""
        if self.original_image:
            self.image = pygame.transform.smoothscale(self.original_image, (self.size, self.size))
        else:
            # Create a blank surface as fallback
            self.image = pygame.Surface((self.size, self.size))
            self.image.fill((200, 0, 0))  # Red for error
    
    def set_position(self, position):
        """Set the token position (center point)."""
        self.position = position
    
    def set_size(self, size):
        """Set the token size and update image."""
        self.size = max(10, min(200, size))  # Clamp between 10 and 200
        self.update_image()
    
    def set_name(self, name):
        """Set the token name."""
        self.name = name
    
    def toggle_visibility(self):
        """Toggle token visibility."""
        self.visible = not self.visible
        return self.visible
    
    def contains_point(self, point):
        """Check if a point is within this circular token."""
        if not self.visible or not self.image:
            return False
            
        # Calculate distance from token center to point
        dx = self.position[0] - point[0]
        dy = self.position[1] - point[1]
        distance_squared = dx*dx + dy*dy
        
        # Check if distance is less than radius
        radius = self.size // 2
        return distance_squared <= radius*radius
    
    def start_drag(self, mouse_pos):
        """Start dragging this token."""
        if not self.visible:
            return False
            
        self.dragging = True
        # Calculate offset between mouse position and token center
        self.drag_offset = (
            self.position[0] - mouse_pos[0],
            self.position[1] - mouse_pos[1]
        )
        return True
    
    def update_drag(self, mouse_pos):
        """Update token position during dragging."""
        if not self.dragging:
            return False
            
        self.position = (
            mouse_pos[0] + self.drag_offset[0],
            mouse_pos[1] + self.drag_offset[1]
        )
        return True
    
    def end_drag(self):
        """End dragging this token."""
        self.dragging = False
        return True
    
    def draw(self, surface):
        """Draw this token to the given surface."""
        if not self.visible or not self.image:
            return
            
        # Calculate position (centered)
        pos = (
            self.position[0] - self.size // 2,
            self.position[1] - self.size // 2
        )
        
        # Create a circular mask
        mask = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(mask, (255, 255, 255, 255), (self.size // 2, self.size // 2), self.size // 2)
        
        # Apply the mask to the token image
        circular_image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        circular_image.blit(self.image, (0, 0))
        circular_image.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        # Draw the circular token
        surface.blit(circular_image, pos)
        
        # Draw selection indicator if selected
        if self.selected:
            pygame.draw.circle(
                surface, 
                (0, 255, 255),  # Cyan
                self.position,  # Center position
                self.size // 2 + 2,  # Radius slightly larger than token
                2  # Border width
            )
            
        # Draw name above token
        if self.name:
            font = pygame.font.SysFont('Arial', 12)
            text = font.render(self.name, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.position[0], pos[1] - 10))
            
            # Draw background for better visibility
            bg_rect = text_rect.inflate(10, 6)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 160))  # Semi-transparent black
            surface.blit(bg_surface, bg_rect.topleft)
            
            # Draw text
            surface.blit(text, text_rect)
    
    def to_dict(self):
        """Convert token to dictionary for serialization."""
        return {
            "image_path": self.image_path,
            "position": self.position,
            "size": self.size,
            "name": self.name,
            "visible": self.visible
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a token from dictionary data."""
        token = cls(
            data["image_path"],
            tuple(data["position"]),
            data["size"],
            data["name"]
        )
        token.visible = data["visible"]
        return token


class TokenManager:
    """
    Manages all tokens on the battlefield.
    """
    
    def __init__(self, screen, config):
        """Initialize the token manager."""
        self.screen = screen
        self.config = config
        self.tokens_directory = config.get("tokens_directory", "assets/tokens")
        
        # Ensure directory exists
        os.makedirs(self.tokens_directory, exist_ok=True)
        
        # Token state
        self.tokens = []
        self.selected_token = None
        self.tokens_visible = True
        self.available_tokens = []
        
        # Load available token images
        self.refresh_token_list()
    
    def refresh_token_list(self):
        """Refresh the list of available token images."""
        self.available_tokens = get_image_files(self.tokens_directory)
    
    def add_token(self, image_path, position, size=50, name=None):
        """Add a new token to the battlefield."""
        # Generate name if not provided
        if not name:
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            existing_count = sum(1 for token in self.tokens if token.name.startswith(base_name))
            if existing_count > 0:
                name = f"{base_name} {existing_count + 1}"
            else:
                name = base_name
        
        # Create and add the token
        token = Token(image_path, position, size, name)
        self.tokens.append(token)
        return token
    
    def remove_token(self, token):
        """Remove a token from the battlefield."""
        if token in self.tokens:
            self.tokens.remove(token)
            if self.selected_token == token:
                self.selected_token = None
            return True
        return False
    
    def get_token_at(self, position):
        """Get the topmost token at the given position."""
        # Check tokens in reverse order (top to bottom)
        for token in reversed(self.tokens):
            if token.contains_point(position):
                return token
        return None
    
    def save_tokens(self, filename):
        """Save tokens to a file."""
        token_data = [token.to_dict() for token in self.tokens]
        
        try:
            with open(filename, 'w') as f:
                json.dump(token_data, f)
            return True
        except Exception as e:
            print(f"Error saving tokens: {e}")
            return False
    
    def load_tokens(self, filename):
        """Load tokens from a file."""
        if not os.path.exists(filename):
            return False
            
        try:
            with open(filename, 'r') as f:
                token_data = json.load(f)
                
            # Clear existing tokens
            self.tokens = []
            
            # Create new tokens
            for data in token_data:
                token = Token.from_dict(data)
                self.tokens.append(token)
                
            return True
        except Exception as e:
            print(f"Error loading tokens: {e}")
            return False
    
    def draw(self):
        """Draw all tokens to the screen."""
        if not self.tokens_visible:
            return
            
        for token in self.tokens:
            token.draw(self.screen)