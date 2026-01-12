from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import threading
import os
from network_utils import get_local_ip

class WebServer:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'vnc_qr_server_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.vnc_callback = None  # Callback to desktop app for VNC connections
        self.setup_routes()
        self.setup_socketio()

    def set_vnc_callback(self, callback):
        """Set callback function for VNC connections."""
        self.vnc_callback = callback

    def set_shutdown_callback(self, callback):
        """Set callback function for server shutdown."""
        self.shutdown_callback = callback

    def setup_routes(self):
        """Setup Flask routes."""

        @self.app.route('/')
        def index():
            """Main web interface."""
            local_ip = get_local_ip()
            saved_servers = self.config_manager.get_saved_servers()
            autostart_supported = self.config_manager.is_autostart_supported()
            return render_template('index.html',
                                 local_ip=local_ip,
                                 saved_servers=saved_servers,
                                 autostart_supported=autostart_supported)

        @self.app.route('/api/settings', methods=['GET', 'POST'])
        def api_settings():
            """API endpoint for settings."""
            if request.method == 'GET':
                return jsonify(self.config_manager.get_settings())
            elif request.method == 'POST':
                settings = request.get_json()
                if autostart_supported:
                    self.config_manager.save_settings(settings)
                return jsonify({'status': 'success'})

        @self.app.route('/api/vnc-clients', methods=['GET'])
        def api_vnc_clients():
            """API endpoint to get available VNC clients."""
            try:
                from cli_vnc_connector import CLIVNCConnector
                connector = CLIVNCConnector()
                available_clients = connector.get_available_clients()
                return jsonify({
                    'status': 'success',
                    'clients': available_clients
                })
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'message': str(e)
                })

        @self.app.route('/api/servers', methods=['GET', 'POST', 'DELETE'])
        def api_servers():
            """API endpoint for VNC servers."""
            if request.method == 'GET':
                return jsonify(self.config_manager.get_saved_servers())
            elif request.method == 'POST':
                server_data = request.get_json()
                self.config_manager.save_server(server_data)
                return jsonify({'status': 'success'})
            elif request.method == 'DELETE':
                server_data = request.get_json()
                self.config_manager.delete_server(server_data)
                return jsonify({'status': 'success'})

    def setup_socketio(self):
        """Setup WebSocket events."""

        @self.socketio.on('connect')
        def handle_connect():
            print("Web client connected")

        @self.socketio.on('disconnect')
        def handle_disconnect():
            print("Web client disconnected")

        @self.socketio.on('vnc_connect')
        def handle_vnc_connect(data):
            """Handle VNC connection request from web client."""
            print(f"VNC connection request: {data}")

            # Save server if requested
            if data.get('save_server', False):
                server_data = {
                    'ip': data['ip'],
                    'port': data['port'],
                    'username': data['username']
                }
                self.config_manager.save_server(server_data)

            # Trigger VNC connection in desktop app
            if self.vnc_callback:
                success = self.vnc_callback(data)
                emit('vnc_status', {'status': 'connected' if success else 'failed'})
            else:
                emit('vnc_status', {'status': 'failed', 'error': 'Desktop app not available'})

        @self.socketio.on('vnc_disconnect')
        def handle_vnc_disconnect():
            """Handle VNC disconnection request."""
            print("VNC disconnect request")
            if self.vnc_callback:
                self.vnc_callback(None)  # None means disconnect
                emit('vnc_status', {'status': 'disconnected'})

        @self.socketio.on('shutdown_server')
        def handle_shutdown_server():
            """Handle server shutdown request."""
            print("Server shutdown requested from web interface")
            emit('shutdown_status', {'status': 'shutting_down'})

            # Schedule shutdown after a brief delay to allow response to be sent
            def delayed_shutdown():
                import time
                time.sleep(2)  # Give time for the response to be sent
                if hasattr(self, 'shutdown_callback') and self.shutdown_callback:
                    self.shutdown_callback()
                else:
                    print("No shutdown callback set, attempting system exit...")
                    import os
                    os._exit(0)

            thread = threading.Thread(target=delayed_shutdown)
            thread.daemon = True
            thread.start()

    def notify_vnc_status(self, status):
        """Notify web clients of VNC status change."""
        self.socketio.emit('vnc_status', {'status': status})

    def run(self):
        """Start the web server."""
        print("Starting VNC QR web server...")

        # Try different host/port combinations
        attempts = [
            ('0.0.0.0', 8080),
            ('localhost', 8080),
            ('127.0.0.1', 8080),
            ('0.0.0.0', 8081),
            ('127.0.0.1', 8081)
        ]

        for host, port in attempts:
            try:
                print(f"Trying {host}:{port}...")
                self.socketio.run(self.app, host=host, port=port, debug=False,
                                use_reloader=False, allow_unsafe_werkzeug=True)
                break  # If successful, exit loop
            except Exception as e:
                print(f"Failed {host}:{port} - {e}")
                continue
        else:
            print("ERROR: Could not start web server on any host/port combination")
            print("Web interface will not be available")
