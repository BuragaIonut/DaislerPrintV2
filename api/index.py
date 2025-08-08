from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL path
        path = urlparse(self.path).path
        
        # Handle different routes
        if path == "/" or path == "/api":
            response = {"message": "Hello from Python backend!"}
        elif path == "/health" or path == "/api/health":
            response = {"status": "healthy"}
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return
        
        # Send successful response
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        # Handle POST requests if needed
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"message": "POST received"}).encode())