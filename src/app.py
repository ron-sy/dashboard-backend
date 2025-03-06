from flask import Flask, jsonify
from flask_cors import CORS
from routes import api
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

def create_app():
    """Initialize and configure Flask application."""
    app = Flask(__name__)
    
    # Enable CORS for frontend with proper configuration
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    print(f"Configuring CORS to allow requests from: {frontend_url}")
    CORS(app, 
         resources={r"/api/*": {
             "origins": [frontend_url],
             "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Accept"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "max_age": 120  # Cache preflight requests for 2 minutes
         }})
    
    # Register API blueprint
    app.register_blueprint(api, url_prefix='/api')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({'status': 'ok'})
    
    return app

app = create_app()

if __name__ == '__main__':
    # Get port from environment variable or use default 5000
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Flask server on port {port}")
    # Disable debug mode in production
    debug_mode = os.getenv("FLASK_ENV", "production") != "production"
    print(f"Debug mode: {debug_mode}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
