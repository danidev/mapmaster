"""
Map management module for MapMaster.
Handles loading, displaying, and switching between battlemaps.
"""

import os
import pygame
import json
from ..utils.image import load_image, scale_image_to_fit, get_image_files

class MapManager:
    """
    Manages battlemap images and their display properties.
    """
    
    def __init__(self, screen, config):
        """Initialize the map manager."""
        self.screen = screen
        self.config = config
        self.maps_directory = config.get("maps_directory", "assets/maps")
        self.annotations_directory = config.get("annotations_directory", "annotations")
        
        # Ensure directories exist
        os.makedirs(self.maps_directory, exist_ok=True)
        os.makedirs(self.annotations_directory, exist_ok=True)
        
        # Map loading and tracking
        self.map_files = []
        self.current_map_index = 0
        self.current_map = None
        self.current_map_surface = None
        self.map_position = (0, 0)
        
        # Annotations
        self.annotations_surface = None
        self.annotation_points = []
        
        # State tracking
        self.drawing_enabled = True
        self.grid_enabled = True  # Force grid to be enabled at startup
        self.grid_size = config.get("grid_size", 50)
        self.grid_color = tuple(config.get("grid_color", [100, 100, 100, 128]))
        self.grid_offset = (0, 0)
        
        # Map-specific grid configurations
        self.map_grid_configs = {}
        self.load_map_grid_configs()
        
        # Load map files
        self.refresh_map_list()
    
    def load_map_grid_configs(self):
        """Load map-specific grid configurations from a JSON file."""
        grid_config_file = os.path.join(self.config.get("annotations_directory", "annotations"), "map_grids.json")
        
        if os.path.exists(grid_config_file):
            try:
                with open(grid_config_file, 'r') as f:
                    self.map_grid_configs = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading map grid configurations: {e}")
                self.map_grid_configs = {}
        else:
            # Create a default empty configuration file
            self.map_grid_configs = {}
            
        # Initialize maps with default grid settings
        self.initialize_default_grid_configs()
        self.save_map_grid_configs()
    
    def initialize_default_grid_configs(self):
        """Initialize default 22x16 grid configurations for all maps."""
        # Get the list of map files
        map_files = get_image_files(self.maps_directory)
        
        # Add default configuration for each map that doesn't have one
        for map_path in map_files:
            map_filename = os.path.basename(map_path)
            if map_filename not in self.map_grid_configs:
                self.map_grid_configs[map_filename] = {
                    'rows': 16,
                    'columns': 22,
                    'offset': (0, 0)
                }
    
    def save_map_grid_configs(self):
        """Save map-specific grid configurations to a JSON file."""
        grid_config_file = os.path.join(self.config.get("annotations_directory", "annotations"), "map_grids.json")
        
        try:
            with open(grid_config_file, 'w') as f:
                json.dump(self.map_grid_configs, f, indent=2)
        except IOError as e:
            print(f"Error saving map grid configurations: {e}")
    
    def refresh_map_list(self):
        """Refresh the list of available map files."""
        self.map_files = get_image_files(self.maps_directory)
        
        # Reset to first map if no current map or out of bounds
        if not self.map_files:
            self.current_map_index = 0
            self.current_map = None
        elif self.current_map not in self.map_files:
            self.current_map_index = 0
            self.load_map(self.map_files[0] if self.map_files else None)
    
    def load_map(self, map_path):
        """Load a specific map by path."""
        if not map_path or not os.path.exists(map_path):
            self.current_map = None
            self.current_map_surface = None
            return False
            
        # Load the map image
        surface = load_image(map_path)
        if not surface:
            return False
            
        # Update state
        self.current_map = map_path
        if self.map_files and map_path in self.map_files:
            self.current_map_index = self.map_files.index(map_path)
        
        # Scale the map to fit the screen if needed
        screen_rect = self.screen.get_rect()
        self.current_map_surface = scale_image_to_fit(surface, screen_rect.width, screen_rect.height)
        
        # Center the map on screen
        map_rect = self.current_map_surface.get_rect()
        self.map_position = ((screen_rect.width - map_rect.width) // 2, 
                            (screen_rect.height - map_rect.height) // 2)
        
        # Create a new annotations surface
        self.annotations_surface = pygame.Surface(self.current_map_surface.get_size(), pygame.SRCALPHA)
        self.annotations_surface.fill((0, 0, 0, 0))  # Transparent
        
        # Reset annotation points
        self.annotation_points = []
        
        # Try to load saved annotations
        self.load_annotations()
        
        # After loading the map, update grid settings based on map-specific config
        self.update_grid_for_current_map()
        
        return True
    
    def next_map(self):
        """Switch to the next map in the list."""
        if not self.map_files:
            return False
            
        self.current_map_index = (self.current_map_index + 1) % len(self.map_files)
        return self.load_map(self.map_files[self.current_map_index])
    
    def previous_map(self):
        """Switch to the previous map in the list."""
        if not self.map_files:
            return False
            
        self.current_map_index = (self.current_map_index - 1) % len(self.map_files)
        return self.load_map(self.map_files[self.current_map_index])
    
    def get_annotation_filename(self):
        """Get the filename for the current map's annotations."""
        if not self.current_map:
            return None
            
        # Get map filename without path or extension
        map_name = os.path.splitext(os.path.basename(self.current_map))[0]
        return os.path.join(self.annotations_directory, f"{map_name}_annotations.json")
    
    def save_annotations(self):
        """Save the current annotations to file."""
        if not self.current_map:
            return False
            
        annotation_file = self.get_annotation_filename()
        if not annotation_file:
            return False
            
        try:
            # Save annotation points (color, size, points)
            with open(annotation_file, 'w') as f:
                json.dump(self.annotation_points, f)
            return True
        except Exception as e:
            print(f"Error saving annotations: {e}")
            return False
    
    def load_annotations(self):
        """Load annotations for the current map."""
        if not self.current_map:
            return False
            
        annotation_file = self.get_annotation_filename()
        if not annotation_file or not os.path.exists(annotation_file):
            return False
            
        try:
            with open(annotation_file, 'r') as f:
                self.annotation_points = json.load(f)
                
            # Redraw the annotations
            self.redraw_annotations()
            return True
        except Exception as e:
            print(f"Error loading annotations: {e}")
            return False
    
    def clear_annotations(self):
        """Clear all annotations for the current map."""
        if self.annotations_surface:
            self.annotations_surface.fill((0, 0, 0, 0))  # Transparent
            self.annotation_points = []
            return True
        return False
    
    def add_annotation_point(self, point, color, size):
        """Add a point to the current annotation stroke."""
        if not self.drawing_enabled or not self.current_map:
            return False
            
        # Add the point to the list
        if not self.annotation_points or self.annotation_points[-1][0] != color or self.annotation_points[-1][1] != size:
            # Start new stroke
            self.annotation_points.append([color, size, [point]])
        else:
            # Add to existing stroke
            self.annotation_points[-1][2].append(point)
            
        # Draw the point
        rel_point = (point[0] - self.map_position[0], point[1] - self.map_position[1])
        pygame.draw.circle(self.annotations_surface, color, rel_point, size // 2)
        
        # If continuing a stroke, draw a line from the previous point
        points = self.annotation_points[-1][2]
        if len(points) > 1:
            prev_point = points[-2]
            prev_rel_point = (prev_point[0] - self.map_position[0], prev_point[1] - self.map_position[1])
            pygame.draw.line(self.annotations_surface, color, prev_rel_point, rel_point, size)
        
        return True
    
    def redraw_annotations(self):
        """Redraw all annotations from saved points."""
        if not self.annotations_surface:
            return
            
        # Clear the surface
        self.annotations_surface.fill((0, 0, 0, 0))
        
        # Redraw each stroke
        for color_str, size, points in self.annotation_points:
            # Convert color from list/string to tuple if needed
            color = tuple(color_str) if isinstance(color_str, list) else color_str
            
            # Draw each point in the stroke
            for i, point in enumerate(points):
                # Adjust point position relative to map
                rel_point = (point[0] - self.map_position[0], point[1] - self.map_position[1])
                
                # Draw the point
                pygame.draw.circle(self.annotations_surface, color, rel_point, size // 2)
                
                # Draw a line to the previous point
                if i > 0:
                    prev_point = points[i-1]
                    prev_rel_point = (prev_point[0] - self.map_position[0], prev_point[1] - self.map_position[1])
                    pygame.draw.line(self.annotations_surface, color, prev_rel_point, rel_point, size)
    
    def toggle_grid(self):
        """Toggle the grid overlay."""
        self.grid_enabled = not self.grid_enabled
        return self.grid_enabled
    
    def set_grid_size(self, size):
        """Set the grid size."""
        self.grid_size = max(10, min(200, size))  # Clamp between 10 and 200
        return self.grid_size
    
    def set_grid_offset(self, offset):
        """Set the grid offset."""
        self.grid_offset = offset
    
    def draw_grid(self):
        """Draw the grid overlay."""
        if not self.current_map_surface:
            return
            
        # Force grid to be drawn regardless of grid_enabled setting during startup
        # After startup, respect the grid_enabled setting
        
        map_rect = self.current_map_surface.get_rect()
        map_rect.topleft = self.map_position
        
        # Create a grid overlay surface
        grid_surface = pygame.Surface(map_rect.size, pygame.SRCALPHA)
        
        # Get map-specific grid config
        map_filename = os.path.basename(self.current_map) if self.current_map else ""
        grid_config = self.map_grid_configs.get(map_filename, {})
        
        # If rows and columns are specified, use them to draw the grid
        if 'rows' in grid_config and 'columns' in grid_config:
            rows = grid_config['rows']
            columns = grid_config['columns']
            
            # Calculate cell size
            cell_width = map_rect.width / columns
            cell_height = map_rect.height / rows
            
            # Draw horizontal lines (rows + 1)
            for i in range(rows + 1):
                y = i * cell_height
                pygame.draw.line(grid_surface, self.grid_color, (0, y), (map_rect.width, y))
            
            # Draw vertical lines (columns + 1)
            for i in range(columns + 1):
                x = i * cell_width
                pygame.draw.line(grid_surface, self.grid_color, (x, 0), (x, map_rect.height))
        else:
            # Fall back to fixed-size grid
            # Draw horizontal lines
            y = self.grid_offset[1] % self.grid_size
            while y < map_rect.height:
                pygame.draw.line(grid_surface, self.grid_color, (0, y), (map_rect.width, y))
                y += self.grid_size
                
            # Draw vertical lines
            x = self.grid_offset[0] % self.grid_size
            while x < map_rect.width:
                pygame.draw.line(grid_surface, self.grid_color, (x, 0), (x, map_rect.height))
                x += self.grid_size
            
        # Blit the grid onto the screen at map position
        self.screen.blit(grid_surface, map_rect.topleft)
    
    def draw(self):
        """Draw the current map to the screen."""
        if not self.current_map_surface:
            # Draw a black background if no map is loaded
            self.screen.fill((0, 0, 0))
            return False
            
        # Draw the map
        self.screen.blit(self.current_map_surface, self.map_position)
        
        # Draw the grid if enabled
        self.draw_grid()  # Always call draw_grid, let it check if grid is enabled
            
        # Draw annotations if any
        if self.annotations_surface:
            self.screen.blit(self.annotations_surface, self.map_position)
            
        return True
    
    def draw_map_only(self):
        """Draw just the current map to the screen without annotations."""
        if not self.current_map_surface:
            # Draw a black background if no map is loaded
            self.screen.fill((0, 0, 0))
            return False
            
        # Draw the map
        self.screen.blit(self.current_map_surface, self.map_position)
        return True
    
    def get_current_filename(self):
        """Get the current map filename."""
        if not self.current_map:
            return None
        return self.current_map
    
    def update_grid_for_current_map(self):
        """Update grid settings for the current map."""
        if not self.current_map:
            return
            
        map_filename = os.path.basename(self.current_map)
        
        # If this map doesn't have a grid config yet, create a default one with 22x16 grid
        if map_filename not in self.map_grid_configs and self.current_map_surface:
            # Default to a 22x16 grid as required
            default_rows = 16
            default_columns = 22
            self.map_grid_configs[map_filename] = {
                'rows': default_rows,
                'columns': default_columns,
                'offset': (0, 0)
            }
            self.save_map_grid_configs()
            
        # Now continue with loading the config as before
        if map_filename in self.map_grid_configs:
            grid_config = self.map_grid_configs[map_filename]
            
            # If rows and columns are specified, calculate grid size
            if 'rows' in grid_config and 'columns' in grid_config:
                rows = max(1, grid_config.get('rows', 16))  # Default to 16 rows
                columns = max(1, grid_config.get('columns', 22))  # Default to 22 columns
                
                if self.current_map_surface:
                    # Calculate grid size based on map dimensions and row/column count
                    map_rect = self.current_map_surface.get_rect()
                    grid_width = map_rect.width / columns
                    grid_height = map_rect.height / rows
                    
                    # Use the smaller dimension to ensure uniform grid cells
                    self.grid_size = min(grid_width, grid_height)
                    
                    # Notify token manager that grid size has changed (if tokens exist)
                    self.update_token_sizes()
            else:
                # Use specified grid size if available
                self.grid_size = grid_config.get('grid_size', self.grid_size)
                self.update_token_sizes()
                
            # Set other grid properties if available
            self.grid_offset = tuple(grid_config.get('offset', self.grid_offset))
    
    def update_token_sizes(self):
        """Update token sizes to match the current grid size."""
        # If we have a token manager attached, update all token sizes
        if hasattr(self, 'token_manager') and self.token_manager:
            self.token_manager.resize_all_tokens(self.grid_size)
    
    def set_map_grid_config(self, rows, columns, offset=(0, 0)):
        """Set grid configuration for the current map."""
        if not self.current_map:
            return False
            
        map_filename = os.path.basename(self.current_map)
        self.map_grid_configs[map_filename] = {
            'rows': rows,
            'columns': columns,
            'offset': offset
        }
        
        # Update grid for current map
        self.update_grid_for_current_map()
        
        # Save configurations
        self.save_map_grid_configs()
        return True

    def set_token_manager(self, token_manager):
        """Connect this map manager to a token manager for resizing tokens."""
        self.token_manager = token_manager
        
        # Set the initial grid size in the token manager
        if hasattr(self, 'grid_size') and self.grid_size > 0:
            self.token_manager.current_grid_size = self.grid_size
            
        # Initial update of token sizes based on grid
        if hasattr(self, 'current_map') and self.current_map:
            self.update_grid_for_current_map()