from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import json
import cgi
import io
import logging
from PIL import Image, ImageDraw

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("print-analyzer")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == "/" or path == "/api":
            response = {"message": "Print Analyzer API - Upload images for analysis"}
        elif path == "/health" or path == "/api/health":
            response = {"status": "healthy"}
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode())
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        # Handle CORS preflight
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        try:
            if path == "/analyze" or path == "/api/analyze":
                self._handle_analyze()
            elif path == "/process" or path == "/api/process":
                self._handle_process()
            else:
                self._send_error(404, "Endpoint not found")
        except Exception as e:
            logger.exception("Error handling request")
            self._send_error(500, str(e))
    
    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_error(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _send_image(self, image_bytes):
        self.send_response(200)
        self.send_header('Content-type', 'image/png')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(image_bytes)
    
    def _parse_multipart(self):
        content_type = self.headers.get('Content-Type', '')
        if not content_type.startswith('multipart/form-data'):
            raise ValueError("Expected multipart/form-data")
        
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            raise ValueError("No content")
        
        # Read the raw data
        raw_data = self.rfile.read(content_length)
        
        # Parse multipart data
        # Create a file-like object for cgi.FieldStorage
        fp = io.BytesIO(raw_data)
        
        # Parse the form data
        form = cgi.FieldStorage(
            fp=fp,
            environ={
                'REQUEST_METHOD': 'POST',
                'CONTENT_TYPE': content_type,
                'CONTENT_LENGTH': str(content_length)
            }
        )
        
        return form
    
    def _handle_analyze(self):
        try:
            form = self._parse_multipart()
            
            # Get file and use_case from form
            if 'file' not in form:
                raise ValueError("No file uploaded")
            if 'use_case' not in form:
                raise ValueError("No use_case provided")
            
            file_item = form['file']
            use_case = form['use_case'].value
            
            if not file_item.file:
                raise ValueError("Invalid file")
            
            # Read image data
            image_data = file_item.file.read()
            
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            width, height = image.size
            aspect_ratio = width / height if height > 0 else 0
            orientation = "landscape" if width > height else "portrait" if height > width else "square"
            
            # Simple analysis without OpenAI (since we don't have API key in this simple setup)
            analysis_result = self._analyze_image_simple(image, use_case, width, height, aspect_ratio, orientation)
            
            self._send_json({"result": analysis_result})
            
        except Exception as e:
            logger.exception("Error in analyze endpoint")
            self._send_error(400, str(e))
    
    def _handle_process(self):
        try:
            form = self._parse_multipart()
            
            # Get file and bleed_px from form
            if 'file' not in form:
                raise ValueError("No file uploaded")
            
            file_item = form['file']
            bleed_px = int(form.get('bleed_px', 30).value) if 'bleed_px' in form else 30
            
            if not file_item.file:
                raise ValueError("Invalid file")
            
            # Read image data
            image_data = file_item.file.read()
            
            # Open image with PIL
            image = Image.open(io.BytesIO(image_data)).convert("RGB")
            
            # Process image (add bleed and cut lines)
            processed_image = self._add_bleed_and_cutlines(image, bleed_px)
            
            # Convert to bytes
            output_buffer = io.BytesIO()
            processed_image.save(output_buffer, format='PNG')
            image_bytes = output_buffer.getvalue()
            
            self._send_image(image_bytes)
            
        except Exception as e:
            logger.exception("Error in process endpoint")
            self._send_error(400, str(e))
    
    def _analyze_image_simple(self, image, use_case, width, height, aspect_ratio, orientation):
        """Simple image analysis without OpenAI API"""
        
        # Basic analysis based on image properties
        analysis_parts = []
        
        analysis_parts.append(f"=== PRINT ANALYSIS FOR: {use_case.upper()} ===\n")
        
        # 1. FORMAT SUITABILITY
        analysis_parts.append("1. FORMAT SUITABILITY:")
        analysis_parts.append(f"   • Dimensions: {width}×{height}px")
        analysis_parts.append(f"   • Aspect ratio: {aspect_ratio:.2f}")
        analysis_parts.append(f"   • Orientation: {orientation}")
        
        # Resolution assessment
        min_dimension = min(width, height)
        if min_dimension < 300:
            analysis_parts.append("   ⚠️  LOW RESOLUTION: Image may appear pixelated when printed")
        elif min_dimension < 600:
            analysis_parts.append("   📋 MODERATE RESOLUTION: Suitable for small prints")
        else:
            analysis_parts.append("   ✅ GOOD RESOLUTION: Suitable for quality printing")
        
        # 2. TEXT ANALYSIS (basic)
        analysis_parts.append("\n2. TEXT ANALYSIS:")
        analysis_parts.append("   • Manual text review recommended")
        analysis_parts.append("   • Ensure text is at least 8pt for readability")
        analysis_parts.append("   • Use high contrast colors for text")
        
        # 3. OBJECT COMPOSITION
        analysis_parts.append("\n3. OBJECT COMPOSITION:")
        analysis_parts.append("   • Review image for multiple distinct elements")
        analysis_parts.append("   • Consider if elements should be separated for different uses")
        
        # 4. POSITIONING & CENTERING
        analysis_parts.append("\n4. POSITIONING & CENTERING:")
        analysis_parts.append("   • Manually verify subject is well-centered")
        analysis_parts.append("   • Check for adequate white space around main elements")
        
        # 5. BLEED REQUIREMENTS
        analysis_parts.append("\n5. BLEED REQUIREMENTS:")
        if use_case.lower() in ['business card', 'postcard', 'flyer', 'poster']:
            analysis_parts.append("   • BLEED REQUIRED: 3-5mm (approximately 30-50px)")
            analysis_parts.append("   • Extends design beyond trim edge")
            analysis_parts.append("   • Use 'Process' button to add bleed automatically")
        elif use_case.lower() in ['sticker', 'label']:
            analysis_parts.append("   • COMPLEX CUTTING: May require die-cutting")
            analysis_parts.append("   • Consider adding bleed for irregular shapes")
        else:
            analysis_parts.append("   • STANDARD BLEED: 3mm recommended for most print jobs")
        
        # Additional recommendations
        analysis_parts.append("\n=== RECOMMENDATIONS ===")
        analysis_parts.append("• Use CMYK color mode for final print files")
        analysis_parts.append("• Save final artwork as high-resolution PDF")
        analysis_parts.append("• Always request a proof before full production")
        
        return "\n".join(analysis_parts)
    
    def _add_bleed_and_cutlines(self, image, bleed_px):
        """Add mirror bleed and cut lines to image"""
        pad = max(0, int(bleed_px))
        w, h = image.size
        
        # Create expanded canvas
        expanded = Image.new("RGB", (w + 2 * pad, h + 2 * pad))
        expanded.paste(image, (pad, pad))
        
        if pad > 0:
            # Left and right bands (mirror horizontally)
            left_band = image.crop((0, 0, pad, h)).transpose(Image.FLIP_LEFT_RIGHT)
            right_band = image.crop((w - pad, 0, w, h)).transpose(Image.FLIP_LEFT_RIGHT)
            expanded.paste(left_band, (0, pad))
            expanded.paste(right_band, (pad + w, pad))
            
            # Top and bottom bands (mirror vertically)
            top_band = image.crop((0, 0, w, pad)).transpose(Image.FLIP_TOP_BOTTOM)
            bottom_band = image.crop((0, h - pad, w, h)).transpose(Image.FLIP_TOP_BOTTOM)
            expanded.paste(top_band, (pad, 0))
            expanded.paste(bottom_band, (pad, pad + h))
            
            # Corners (double reflection ~ rotate 180)
            tl = image.crop((0, 0, pad, pad)).transpose(Image.ROTATE_180)
            tr = image.crop((w - pad, 0, w, pad)).transpose(Image.ROTATE_180)
            bl = image.crop((0, h - pad, pad, h)).transpose(Image.ROTATE_180)
            br = image.crop((w - pad, h - pad, w, h)).transpose(Image.ROTATE_180)
            expanded.paste(tl, (0, 0))
            expanded.paste(tr, (pad + w, 0))
            expanded.paste(bl, (0, pad + h))
            expanded.paste(br, (pad + w, pad + h))
        
        # Draw cutting rectangle (green)
        draw = ImageDraw.Draw(expanded)
        rect = (pad, pad, pad + w - 1, pad + h - 1)
        draw.rectangle(rect, outline=(60, 235, 120), width=2)
        
        return expanded