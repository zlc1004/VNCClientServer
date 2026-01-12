# VNCClientServer

VNCClientServer is a Python application that displays a fullscreen QR code for mobile access to VNC remote desktop connections. Scan the QR code with your mobile device to access a web interface for controlling VNC connections in real-time.

## Installation

Clone the repository and run the appropriate startup script for your platform.

```bash
# macOS
./run_vnc_qr_server.sh

# Windows
./run_vnc_qr_server.bat
```

## Usage

```bash
# Start the server
python main.py

# 1. Scan the QR code displayed on your desktop with your mobile device
# 2. Enter VNC server details in the mobile web interface
# 3. Connect to control the VNC session remotely
# 4. The desktop will switch between QR code and VNC display automatically
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to test the application on both macOS and Windows platforms.

## License

[MIT](https://choosealicense.com/licenses/mit/)
