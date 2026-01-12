import socket
import subprocess
import re
import platform

def get_local_ip():
    """Get the local IP address (not loopback)."""
    try:
        # Method 1: Connect to a remote address and get local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            if not local_ip.startswith('127.'):
                return local_ip
    except Exception:
        pass
    
    try:
        # Method 2: Use hostname resolution
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        if not local_ip.startswith('127.'):
            return local_ip
    except Exception:
        pass
    
    # Method 3: Parse network interfaces (platform-specific)
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return get_mac_ip()
    elif system == "Windows":
        return get_windows_ip()
    else:
        return get_linux_ip()

def get_mac_ip():
    """Get IP address on macOS."""
    try:
        # Use ifconfig to get network interfaces
        result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
        output = result.stdout
        
        # Look for inet addresses that are not loopback
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if 'inet ' in line and '127.0.0.1' not in line:
                # Extract IP address
                ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    ip = ip_match.group(1)
                    # Skip link-local addresses
                    if not ip.startswith('169.254.'):
                        return ip
                        
    except Exception as e:
        print(f"Error getting IP via ifconfig: {e}")
    
    # Fallback to localhost
    return "127.0.0.1"

def get_windows_ip():
    """Get IP address on Windows."""
    try:
        result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
        output = result.stdout
        
        # Look for IPv4 addresses that are not loopback
        ip_pattern = r'IPv4 Address[.\s]*:\s*(\d+\.\d+\.\d+\.\d+)'
        matches = re.findall(ip_pattern, output)
        
        for ip in matches:
            if not ip.startswith('127.') and not ip.startswith('169.254.'):
                return ip
                
    except Exception as e:
        print(f"Error getting IP via ipconfig: {e}")
    
    # Fallback to localhost
    return "127.0.0.1"

def get_linux_ip():
    """Get IP address on Linux."""
    try:
        # Try ip command first
        result = subprocess.run(['ip', 'route', 'get', '8.8.8.8'], 
                              capture_output=True, text=True, timeout=5)
        output = result.stdout
        
        # Parse the output to get source IP
        src_match = re.search(r'src\s+(\d+\.\d+\.\d+\.\d+)', output)
        if src_match:
            return src_match.group(1)
            
    except Exception:
        pass
    
    try:
        # Fallback to ifconfig
        result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
        output = result.stdout
        
        # Look for inet addresses that are not loopback
        for line in output.split('\n'):
            if 'inet ' in line and '127.0.0.1' not in line:
                ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    ip = ip_match.group(1)
                    if not ip.startswith('169.254.'):
                        return ip
                        
    except Exception as e:
        print(f"Error getting IP via ifconfig: {e}")
    
    # Fallback to localhost
    return "127.0.0.1"

def is_port_available(port, host='localhost'):
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0
    except Exception:
        return False

def get_network_interfaces():
    """Get all network interfaces and their IP addresses."""
    interfaces = []
    system = platform.system()
    
    try:
        if system == "Darwin" or system == "Linux":
            # Unix-like systems
            result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
            output = result.stdout
            
            # Parse the output to extract interface information
            current_interface = None
            for line in output.split('\n'):
                line = line.strip()
                
                # Look for interface names (lines that don't start with whitespace)
                if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
                    current_interface = line.split(':')[0].strip()
                    continue
                    
                # Look for inet addresses
                if 'inet ' in line and current_interface:
                    ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        ip = ip_match.group(1)
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            interfaces.append({
                                'name': current_interface,
                                'ip': ip
                            })
                            
        elif system == "Windows":
            # Windows command to get network interfaces
            result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, shell=True)
            output = result.stdout
            
            # Parse the output to extract interface information
            current_interface = None
            for line in output.split('\n'):
                line = line.strip()
                
                # Look for adapter names
                if 'adapter' in line.lower() and ':' in line:
                    current_interface = line.split(':')[0].strip()
                    continue
                    
                # Look for IPv4 addresses
                if 'IPv4 Address' in line and current_interface:
                    ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        ip = ip_match.group(1)
                        if not ip.startswith('127.') and not ip.startswith('169.254.'):
                            interfaces.append({
                                'name': current_interface,
                                'ip': ip
                            })
                            
    except Exception as e:
        print(f"Error getting network interfaces: {e}")
        
    return interfaces

def test_connectivity(host="8.8.8.8", port=53, timeout=3):
    """Test internet connectivity."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return False
