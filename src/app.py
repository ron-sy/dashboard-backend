from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Debug prints for environment setup
print("\n=== DEBUG: Environment Setup ===")
print(f"Current working directory: {os.getcwd()}")
print(f"__file__ path: {__file__}")
print(f"Parent directory: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
print(f"Looking for .env at path: {dotenv_path}")
print(f"Does .env exist? {os.path.exists(dotenv_path)}")
load_dotenv(dotenv_path)

# Print environment variables
print("\n=== DEBUG: Environment Variables ===")
print(f"MANDRILL_API_KEY present: {'MANDRILL_API_KEY' in os.environ}")
if 'MANDRILL_API_KEY' in os.environ:
    key = os.environ['MANDRILL_API_KEY']
    print(f"MANDRILL_API_KEY value: {key[:4]}...{key[-4:]}")
print("=====================================\n")

from src.routes import api

# Updated for GitHub Actions CI/CD integration - Automatic deployment
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
    try:
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        allowed_origins = [
            frontend_url, 
            "https://app.syntheticteams.com",
            "https://dashboard-55056.web.app",
            # Add wildcard for development
            "http://localhost:*"
        ]
        print(f"Configuring CORS to allow requests from: {allowed_origins}")
        CORS(app, 
             resources={r"/*": {
                 "origins": allowed_origins,
                 "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                 "allow_headers": ["Content-Type", "Authorization", "Accept"],
                 "expose_headers": ["Content-Type", "Authorization"],
                 "supports_credentials": True,
                 "max_age": 120  # Cache preflight requests for 2 minutes
             }})
    except Exception as e:
        print(f"WARNING: Error configuring CORS: {str(e)}")
        # Fall back to a more permissive CORS policy if there's an error
        CORS(app)
    
    # Register API blueprint
    app.register_blueprint(api, url_prefix='/api')
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        try:
            # Basic operational check
            return jsonify({
                'status': 'ok',
                'version': '1.0.0',
                'environment': os.getenv('FLASK_ENV', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }), 200
        except Exception as e:
            # Log any errors but still return a response
            print(f"Health check error: {str(e)}")
            return jsonify({
                'status': 'degraded',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 200  # Still return 200 to keep the service running
    
    return app

if __name__ == "__main__":
    # Get the PORT environment variable, default to 5001 if not set
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    
    print(f"Starting Flask server on port {port}")
    print(f"Debug mode: {debug}")
    
    app = create_app()
    app.run(host='0.0.0.0', port=port, debug=debug)
else:
    # For Gunicorn
    app = create_app()
