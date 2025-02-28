import os
import sys
import random
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore, auth

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models import Company, OnboardingStep, OnboardingStatus, DEFAULT_ONBOARDING_STEPS
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(dotenv_path)

# Firebase configuration
PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "dashboard-55056")
SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT", None)

def initialize_firebase():
    """Initialize Firebase with credentials"""
    try:
        # Check if service account path is provided
        if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
            cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
            firebase_admin.initialize_app(cred)
            print(f"Firebase initialized with service account: {SERVICE_ACCOUNT_PATH}")
        else:
            # Try to initialize with just the project ID in development mode
            firebase_admin.initialize_app(options={
                'projectId': PROJECT_ID,
            })
            print(f"Firebase initialized with project ID in development mode: {PROJECT_ID}")
        
        # Test if we can access Firestore
        db = firestore.client()
        return db
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        print("\nTROUBLESHOOTING:")
        print("1. Make sure you have the Firebase service account JSON file")
        print("2. Update your .env file with the correct path to the service account JSON")
        print("3. Set up Application Default Credentials: https://cloud.google.com/docs/authentication/external/set-up-adc")
        print("4. Login with Firebase CLI: firebase login")
        sys.exit(1)

# Mock company names
COMPANY_NAMES = [
    "TechNova Solutions",
    "Alpha Innovations",
    "Quantum Dynamics",
    "Nexus Enterprises",
    "Horizon Technologies",
    "Pioneer Systems",
    "Vertex AI Labs",
    "Fusion Analytics",
    "Stellar Computing",
    "Apex Digital Solutions"
]

# Mock user emails and passwords
MOCK_USERS = [
    {"email": "admin@example.com", "password": "Password123", "display_name": "Admin User"},
    {"email": "john.doe@technova.com", "password": "Password123", "display_name": "John Doe"},
    {"email": "sarah.smith@alpha.com", "password": "Password123", "display_name": "Sarah Smith"},
    {"email": "michael.johnson@quantum.com", "password": "Password123", "display_name": "Michael Johnson"},
    {"email": "emily.williams@nexus.com", "password": "Password123", "display_name": "Emily Williams"}
]

def create_mock_users():
    """Create mock users in Firebase Authentication"""
    print("Creating mock users in Firebase Authentication...")
    created_users = []
    
    for user_data in MOCK_USERS:
        try:
            # Check if user already exists
            try:
                existing_user = auth.get_user_by_email(user_data["email"])
                print(f"User {user_data['email']} already exists with UID: {existing_user.uid}")
                created_users.append(existing_user.uid)
                continue
            except auth.UserNotFoundError:
                pass
                
            # Create user
            user = auth.create_user(
                email=user_data["email"],
                password=user_data["password"],
                display_name=user_data["display_name"],
                email_verified=True
            )
            created_users.append(user.uid)
            print(f"Created user: {user.uid} ({user_data['email']})")
        except Exception as e:
            print(f"Error creating user {user_data['email']}: {e}")
    
    print(f"Mock users creation completed. Created/Found {len(created_users)} users.")
    return created_users

def generate_random_steps():
    """Generate a copy of default steps with random statuses"""
    steps = []
    statuses = list(OnboardingStatus)
    
    for step in DEFAULT_ONBOARDING_STEPS:
        # Copy the step and assign a random status
        random_status = random.choice(statuses)
        
        # Set a random update date within the last 30 days
        random_days = random.randint(0, 30)
        update_date = datetime.now() - timedelta(days=random_days)
        
        new_step = OnboardingStep(
            id=step.id,
            name=step.name,
            description=step.description,
            status=random_status,
            updated_at=update_date
        )
        steps.append(new_step)
    
    return steps

def create_mock_companies(db):
    """Create mock companies in Firestore"""
    print("Creating mock companies in Firestore...")
    
    # Get companies collection reference
    companies_ref = db.collection('companies')
    created_companies = []
    
    # Check if we already have companies in the database
    existing_companies = list(companies_ref.limit(1).stream())
    if existing_companies:
        print("Found existing companies in the database. Do you want to:")
        print("1. Skip creation (default)")
        print("2. Add more companies")
        print("3. Delete all and recreate")
        choice = input("Enter your choice (1-3): ").strip() or "1"
        
        if choice == "1":
            print("Skipping company creation.")
            return []
        elif choice == "3":
            print("Deleting all existing companies...")
            # Get all company documents
            all_companies = list(companies_ref.stream())
            # Delete each document
            for doc in all_companies:
                doc.reference.delete()
                print(f"Deleted company: {doc.id}")
    
    for company_name in COMPANY_NAMES:
        try:
            # Create a random date within the last 90 days
            random_days = random.randint(0, 90)
            created_date = datetime.now() - timedelta(days=random_days)
            
            # Create company with random onboarding step statuses
            company = Company(
                id='',  # Firestore will generate an ID
                name=company_name,
                onboarding_steps=generate_random_steps(),
                created_at=created_date
            )
            
            # Add to Firestore
            company_ref = companies_ref.document()
            company_ref.set(company.to_dict())
            created_companies.append(company_ref.id)
            print(f"Created company: {company_name} with ID: {company_ref.id}")
            
        except Exception as e:
            print(f"Error creating company {company_name}: {e}")
    
    print(f"Mock companies creation completed. Created {len(created_companies)} companies.")
    return created_companies

def main():
    """Main function to create all mock data"""
    print("Starting mock data generation in Firebase...")
    
    # Initialize Firebase
    db = initialize_firebase()
    
    # Create mock users
    try:
        user_ids = create_mock_users()
    except Exception as e:
        print(f"Error creating mock users: {e}")
    
    # Create mock companies
    try:
        company_ids = create_mock_companies(db)
    except Exception as e:
        print(f"Error creating mock companies: {e}")
    
    print("Mock data generation completed.")
    
    # Display summary
    if 'user_ids' in locals() and len(user_ids) > 0:
        print(f"\nCreated/found {len(user_ids)} users in Firebase Authentication.")
        print("Test login with: admin@example.com / Password123")
    
    if 'company_ids' in locals() and len(company_ids) > 0:
        print(f"\nCreated {len(company_ids)} companies in Firestore.")
        print(f"First company ID: {company_ids[0] if company_ids else 'None'}")

if __name__ == "__main__":
    main() 