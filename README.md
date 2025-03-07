# MapMaster

A local battlemap tool for tabletop RPGs with networked client support.

## Overview

MapMaster is a lightweight tool designed for Game Masters to display battle maps on a shared screen or networked devices. It allows for easy map navigation, token placement, and grid management without requiring an internet connection.

## Features

- **Map Display**: Load and display battle maps from your local storage
- **Token Management**: Place, move, and remove tokens on the battle map
- **Grid Overlay**: Toggleable grid with customizable size
- **Network Streaming**: Share your battle map with players via web browsers or dedicated clients
- **Raspberry Pi Client**: Optimized client for displaying maps on a Raspberry Pi

## Installation

### Prerequisites

- Python 3.6 or higher
- Pygame
- Flask (for server functionality)
- OpenCV (for image processing)
- Pillow (for the Raspberry Pi client)

### Setup

1. Clone the repository:
  ```
  git clone https://github.com/yourusername/mapmaster.git
  cd mapmaster
  ```

2. Create and activate a virtual environment:
  ```
  python -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```

3. Install the requirements:
  ```
  pip install pygame flask opencv-python pillow
  ```

## Usage

### Starting the Main Application

Run the main application using:

  ```
  python -m mapmaster.main
  ```

Or use the provided script:
  
  ```
  ./scripts/run.sh
  ```

### Controls
- Left-click on empty space: Add a new token
- Left-click on token: Select and drag token
- Right-click: Deselect token
- Arrow keys/Space: Change maps
- G: Toggle grid overlay
- F3: Show/hide tokens
-- F11: Toggle fullscreen
- ESC: Exit application
- DELETE: Remove selected token

### Web Client
When the application starts, it will display a URL that players can use to connect via a web browser.

Example: http://192.168.1.100:5000

### Raspberry Pi Client
To display the map on a dedicated Raspberry Pi screen:

1. Copy the rpi_client.py script to your Raspberry Pi
2. Install the required packages:
  ```
  pip3 install pygame pillow requests
  ```
3. Run the client, pointing to your MapMaster server:
  ```
  python3 rpi_client.py http://server_ip:port/stream
  ```

## Project Status

MapMaster is currently in active development. The following features are implemented:

- ✅ Basic map loading and display
- ✅ Token placement and movement
- ✅ Grid overlay
- ✅ Web client streaming
- ✅ Raspberry Pi optimized client

Upcoming features:

- ⬜ Token initiative tracking
- ⬜ Fog of war
- ⬜ Distance measurement
- ⬜ Persistence: Save and load map and token states

## Directory Structure

```
mapmaster/
├── mapmaster/            # Main package
│   ├── __init__.py
│   ├── main.py           # Entry point
│   ├── battle/           # Battle-related modules
│   ├── server/           # Web server modules
│   └── ui/               # User interface modules
├── assets/               # Assets directory
│   ├── maps/             # Map images
│   └── tokens/           # Token images
├── scripts/              # Utility scripts
└── templates/            # Web templates
```

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## Support
If you find this tool useful, consider supporting its development:

<a href="https://www.paypal.com/donate?business=lodevalm@gmail.com&item_name=Support+MapMaster+Development"><img src="https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif" alt="Donate"></a>

## License
This project is licensed under the MIT License - see the LICENSE file for details.
