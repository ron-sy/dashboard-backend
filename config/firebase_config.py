import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from dotenv import load_dotenv
import json

# Load environment variables from the parent directory
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Firebase configuration
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "dashboard-55056")
SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT", None)
# Always use production Firebase, regardless of environment setting
USE_EMULATOR = False  # Force to False to ensure production Firebase
FIRESTORE_EMULATOR_HOST = os.getenv("FIRESTORE_EMULATOR_HOST", "localhost:8080")

def initialize_firebase():
    """Initialize Firebase Admin SDK with appropriate credentials."""
    try:
        print("\n=== FIREBASE INITIALIZATION ===")
        print(f"Project ID: {PROJECT_ID}")
        print(f"Using Production Firebase: {not USE_EMULATOR}")
        
        # Check if app is already initialized
        try:
            app = firebase_admin.get_app()
            print("Firebase app already initialized")
            return firestore.client()
        except ValueError:
            pass  # App not initialized yet
            
        # Check if service account path is provided and exists
        if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
            print(f"Initializing Firebase with service account: {SERVICE_ACCOUNT_PATH}")
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
        else:
            # Try to initialize with Application Default Credentials
            try:
                print(f"Initializing Firebase with Application Default Credentials for project: {PROJECT_ID}")
                firebase_admin.initialize_app(options={
                    'projectId': PROJECT_ID,
                })
                print("Successfully initialized with Application Default Credentials")
            except Exception as adc_error:
                print(f"Failed to initialize with Application Default Credentials: {adc_error}")
                print("Attempting to use GOOGLE_APPLICATION_CREDENTIALS environment variable")
                
                # As a last resort, if there's a GOOGLE_APPLICATION_CREDENTIALS in environment
                creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
                if creds_path and os.path.exists(creds_path):
                    cred = credentials.Certificate(creds_path)
                    firebase_admin.initialize_app(cred)
                    print(f"Successfully initialized with GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")
                else:
                    raise Exception("No valid credentials found")
        
        # Initialize Firestore client
        db = firestore.client()
        
        # Always using production Firebase
        print("Using production Firebase services")
        
        print("Firebase initialized successfully")
        print("================================\n")
        return db
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        print("\nTROUBLESHOOTING TIPS:")
        print("1. Make sure you have the Firebase service account JSON file")
        print("2. Update your .env file with the correct path to the service account JSON")
        print("3. Set up Application Default Credentials: https://cloud.google.com/docs/authentication/external/set-up-adc")
        print("4. Or run: gcloud auth application-default login")
        print("5. For production, create a service account with appropriate permissions in the Firebase console")
        return None

# Initialize Firestore
db = initialize_firebase()
