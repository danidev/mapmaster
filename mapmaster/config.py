import os
import json
import shutil

# Default configuration
DEFAULT_CONFIG = {
    "window_width": 1280,
    "window_height": 720,
    "fullscreen": False,
    "maps_directory": "assets/maps",
    "tokens_directory": "assets/tokens",
    "annotations_directory": "annotations",
    "port": 5000,
    "grid_enabled": False,
    "grid_size": 50,
    "grid_color": [100, 100, 100, 128],  # RGBA
}

CONFIG_FILE = "config.json"

class Config:
    """Configuration manager for MapMaster."""
    
    def __init__(self):
        self.data = {}
        self.load()
        
    def load(self):
        """Load configuration from file or create default."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    self.data = json.load(f)
                # Update with any missing default values
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self.data:
                        self.data[key] = value
            else:
                self.data = DEFAULT_CONFIG.copy()
                self.save()  # Create the file with default values
                
            # Create directories if they don't exist
            for dir_key in ["maps_directory", "tokens_directory", "annotations_directory"]:
                os.makedirs(self.data[dir_key], exist_ok=True)
                
        except Exception as e:
            print(f"Error loading config: {e}. Using defaults.")
            self.data = DEFAULT_CONFIG.copy()
            
    def save(self):
        """Save current configuration to file."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get a configuration value."""
        return self.data.get(key, default)
    
    def set(self, key, value):
        """Set a configuration value and save."""
        self.data[key] = value
        self.save()