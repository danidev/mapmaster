"""
Flask server for MapMaster.
Provides a web interface for players to connect to.
"""

import cv2
import numpy as np
from flask import Flask, Response, render_template, send_from_directory, request, jsonify
import pygame
import os
from ..utils.image import surface_to_bytes

def create_app(app_instance):
    """Create the Flask application."""
    flask_app = Flask(__name__, 
                     static_folder="../../static",
                     template_folder="../../templates")
    
    # Store a reference to the main application
    flask_app.app_instance = app_instance
    
    # Define routes
    @flask_app.route('/')
    def index():
        """Render the main page."""
        return render_template('index.html')
    
    @flask_app.route('/master')
    def master():
        """Render the game master page."""
        return render_template('master.html')
    
    @flask_app.route('/stream')
    def stream():
        """Stream the current screen."""
        return Response(generate_frames(flask_app.app_instance),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @flask_app.route('/static/<path:filename>')
    def serve_static(filename):
        """Serve static files."""
        return send_from_directory(flask_app.static_folder, filename)
    
    @flask_app.route('/api/tokens', methods=['GET'])
    def get_tokens():
        """Get a list of available tokens."""
        token_manager = flask_app.app_instance.token_manager
        token_manager.refresh_token_list()
        
        tokens = []
        for path in token_manager.available_tokens:
            name = os.path.splitext(os.path.basename(path))[0]
            tokens.append({
                'name': name,
                'path': path,
                'url': f'/api/token_image?path={path}'
            })
            
        return jsonify({'tokens': tokens})
    
    @flask_app.route('/api/active_tokens', methods=['GET'])
    def get_active_tokens():
        """Get a list of tokens currently on the map."""
        token_manager = flask_app.app_instance.token_manager
        
        tokens = []
        for token in token_manager.tokens:
            tokens.append({
                'name': token.name,
                'position': token.position,
                'size': token.size,
                'visible': token.visible
            })
            
        return jsonify({'tokens': tokens})
    
    @flask_app.route('/api/add_token', methods=['POST'])
    def add_token():
        """Add a token to the map."""
        data = request.json
        token_path = data.get('token_path')
        position = data.get('position', [400, 300])  # Default to center
        
        token_manager = flask_app.app_instance.token_manager
        token = token_manager.add_token(token_path, position)
        
        if token:
            return jsonify({'success': True, 'token': {
                'name': token.name,
                'position': token.position
            }})
        else:
            return jsonify({'success': False, 'error': 'Failed to add token'})
    
    @flask_app.route('/api/move_token', methods=['POST'])
    def move_token():
        """Move a token on the map."""
        data = request.json
        token_name = data.get('token_name')
        position = data.get('position')
        
        if not token_name or not position:
            return jsonify({'success': False, 'error': 'Missing token name or position'})
        
        token_manager = flask_app.app_instance.token_manager
        
        # Find token by name
        found = False
        for token in token_manager.tokens:
            if token.name == token_name:
                token.set_position(position)
                found = True
                break
        
        if found:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Token not found'})
    
    @flask_app.route('/api/remove_token', methods=['POST'])
    def remove_token():
        """Remove a token from the map."""
        data = request.json
        token_name = data.get('token_name')
        
        if not token_name:
            return jsonify({'success': False, 'error': 'Missing token name'})
        
        token_manager = flask_app.app_instance.token_manager
        
        # Find token by name
        for token in token_manager.tokens:
            if token.name == token_name:
                token_manager.remove_token(token)
                return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Token not found'})
    
    @flask_app.route('/api/token_image')
    def token_image():
        """Serve a token image."""
        path = request.args.get('path')
        if not path or not os.path.exists(path):
            return "Token not found", 404
        
        return send_from_directory(os.path.dirname(path), os.path.basename(path))
    
    @flask_app.route('/api/next_map', methods=['POST'])
    def next_map():
        """Switch to the next map."""
        map_manager = flask_app.app_instance.map_manager
        success = map_manager.next_map()
        return jsonify({'success': success})

    @flask_app.route('/api/prev_map', methods=['POST'])
    def prev_map():
        """Switch to the previous map."""
        map_manager = flask_app.app_instance.map_manager
        success = map_manager.previous_map()
        return jsonify({'success': success})

    @flask_app.route('/api/toggle_grid', methods=['POST'])
    def toggle_grid():
        """Toggle the grid overlay."""
        map_manager = flask_app.app_instance.map_manager
        enabled = map_manager.toggle_grid()
        return jsonify({'success': True, 'grid_enabled': enabled})

    @flask_app.route('/api/toggle_fullscreen', methods=['POST'])
    def toggle_fullscreen():
        """Toggle fullscreen mode."""
        success = flask_app.app_instance.toggle_fullscreen()
        return jsonify({'success': True, 'fullscreen': success})

    return flask_app

def generate_frames(app_instance):
    """Generate video frames for streaming."""
    while True:
        # Get the current screen from the application
        screen = app_instance.get_screen_image()
        if screen is None:
            continue
            
        # Convert Pygame surface to bytes
        frame = surface_to_bytes(screen)
        
        # Convert to JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_bytes = buffer.tobytes()
        
        # Yield the frame in the MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def start_server(app, host, port):
    """Start the Flask server."""
    app.run(host=host, port=port, threaded=True)