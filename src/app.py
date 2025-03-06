from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os
from dotenv import load_dotenv
import json

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.routes import api

# Updated for GitHub Actions CI/CD integration - Automatic deployment
# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Load secrets from GCP Secret Manager if in Cloud Run environment
def load_gcp_secrets():
    mandrill_api_key_path = os.getenv("MANDRILL_KEY_PATH")
    firebase_credentials_path = os.getenv("FIREBASE_CREDS_PATH")
    
    if mandrill_api_key_path and os.path.exists(mandrill_api_key_path):
        try:
            with open(mandrill_api_key_path, 'r') as f:
                mandrill_api_key = f.read().strip()
                if mandrill_api_key.startswith('mandrill_api_key:'):
                    mandrill_api_key = mandrill_api_key.split('mandrill_api_key:')[1].strip()
                os.environ['MANDRILL_API_KEY'] = mandrill_api_key
                print("Loaded Mandrill API key from GCP Secret Manager")
        except Exception as e:
            print(f"Error loading Mandrill API key from GCP Secret Manager: {e}")
    
    if firebase_credentials_path and os.path.exists(firebase_credentials_path):
        try:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = firebase_credentials_path
            print(f"Set GOOGLE_APPLICATION_CREDENTIALS to {firebase_credentials_path}")
        except Exception as e:
            print(f"Error setting GOOGLE_APPLICATION_CREDENTIALS: {e}")

# Load GCP secrets if in Cloud Run environment
load_gcp_secrets()

def create_app():
    """Initialize and configure Flask application."""
    app = Flask(__name__)
    
    # Enable CORS for frontend with proper configuration
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    print(f"Configuring CORS to allow requests from: {frontend_url}")
    CORS(app, 
         resources={r"/*": {
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
