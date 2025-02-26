#!/usr/bin/env python3
import os
import sys
import subprocess
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

def print_header(text):
    print("\n" + "=" * 80)
    print(f" {text}")
    print("=" * 80 + "\n")

def check_firebase_cli():
    """Check if Firebase CLI is installed"""
    try:
        result = subprocess.run(['firebase', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Firebase CLI is installed: {result.stdout.strip()}")
            return True
        else:
            print("❌ Firebase CLI is installed but not working properly.")
            return False
    except FileNotFoundError:
        print("❌ Firebase CLI is not installed.")
        return False

def install_firebase_cli():
    """Install Firebase CLI"""
    print("Installing Firebase CLI...")
    try:
        subprocess.run(['npm', 'install', '-g', 'firebase-tools'], check=True)
        print("✅ Firebase CLI installed successfully.")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Firebase CLI.")
        return False

def login_to_firebase():
    """Login to Firebase"""
    print("Logging in to Firebase...")
    try:
        subprocess.run(['firebase', 'login'], check=True)
        print("✅ Logged in to Firebase successfully.")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to log in to Firebase.")
        return False

def setup_project_credentials():
    """Set up project credentials"""
    project_id = os.getenv("FIREBASE_PROJECT_ID", "dashboard-55056")
    
    print(f"Setting up credentials for project: {project_id}")
    print("\nYou need a service account key file to authenticate with Firebase Admin SDK.")
    print("You have two options:")
    print("1. Generate a new service account key from the Firebase console")
    print("2. Use Application Default Credentials (ADC) for local development")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == "1":
        # Open Firebase console to create a service account key
        console_url = f"https://console.firebase.google.com/project/{project_id}/settings/serviceaccounts/adminsdk"
        print(f"\nOpening Firebase console: {console_url}")
        print("Please follow these steps:")
        print("1. Click 'Generate new private key'")
        print("2. Save the file in a secure location")
        webbrowser.open(console_url)
        
        # Ask for the path to the downloaded key file
        key_path = input("\nEnter the path to the downloaded service account key file: ").strip()
        key_path = os.path.abspath(os.path.expanduser(key_path))
        
        if not os.path.exists(key_path):
            print(f"❌ File not found: {key_path}")
            return False
        
        # Create a secure location for the key file
        config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
        os.makedirs(config_dir, exist_ok=True)
        key_dest = os.path.join(config_dir, 'firebase-service-account.json')
        
        # Copy the key file
        try:
            with open(key_path, 'r') as src, open(key_dest, 'w') as dest:
                dest.write(src.read())
            print(f"✅ Service account key copied to: {key_dest}")
            
            # Update .env file
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
            with open(env_path, 'r') as f:
                env_content = f.read()
            
            # Replace or add the service account path
            if "FIREBASE_SERVICE_ACCOUNT=" in env_content:
                env_content = env_content.replace("# FIREBASE_SERVICE_ACCOUNT=", f"FIREBASE_SERVICE_ACCOUNT={key_dest}")
                env_content = env_content.replace("FIREBASE_SERVICE_ACCOUNT=", f"FIREBASE_SERVICE_ACCOUNT={key_dest}")
            else:
                env_content += f"\nFIREBASE_SERVICE_ACCOUNT={key_dest}\n"
            
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            print(f"✅ Updated .env file with service account path")
            return True
            
        except Exception as e:
            print(f"❌ Error copying service account key: {e}")
            return False
            
    elif choice == "2":
        # Set up Application Default Credentials
        print("\nSetting up Application Default Credentials (ADC)...")
        try:
            subprocess.run(['gcloud', 'auth', 'application-default', 'login'], check=True)
            print("✅ ADC set up successfully.")
            return True
        except FileNotFoundError:
            print("❌ gcloud CLI not found. Please install it first:")
            print("https://cloud.google.com/sdk/docs/install")
            return False
        except subprocess.CalledProcessError:
            print("❌ Failed to set up ADC.")
            return False
    else:
        print("❌ Invalid choice.")
        return False

def main():
    print_header("Firebase Credentials Setup")
    
    # Check if Firebase CLI is installed
    if not check_firebase_cli():
        install = input("Do you want to install Firebase CLI? (y/n): ").strip().lower()
        if install == 'y':
            if not install_firebase_cli():
                print("Please install Firebase CLI manually:")
                print("npm install -g firebase-tools")
                return
        else:
            print("Please install Firebase CLI manually before continuing.")
            return
    
    # Login to Firebase
    login = input("Do you want to log in to Firebase? (y/n): ").strip().lower()
    if login == 'y':
        if not login_to_firebase():
            print("Please log in to Firebase manually:")
            print("firebase login")
    
    # Set up project credentials
    if not setup_project_credentials():
        print("\n❌ Failed to set up project credentials.")
        return
    
    print_header("Firebase Credentials Setup Complete")
    print("You can now run the mock data generation script:")
    print("python scripts/generate_mock_data.py")

if __name__ == "__main__":
    main() 