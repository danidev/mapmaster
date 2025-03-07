import socket
import netifaces

def get_local_ip():
    """Get the local IP address of this machine on the LAN."""
    try:
        # Try to get the preferred interface
        interfaces = netifaces.interfaces()
        for interface in interfaces:
            if interface.startswith(('en', 'eth', 'wlan')):  # Common interface names
                addresses = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addresses:
                    for link in addresses[netifaces.AF_INET]:
                        ip = link['addr']
                        if not ip.startswith('127.'):  # Skip localhost
                            return ip
        
        # Fallback method
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.1)
        s.connect(("8.8.8.8", 80))  # Google's DNS server
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return "127.0.0.1"  # Return localhost as fallback

def find_free_port(start_port=5000, max_attempts=100):
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return start_port  # Fall back to the start port