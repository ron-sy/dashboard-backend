import os
import sys
import uuid
from datetime import datetime

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models import OnboardingStep, OnboardingStatus
from config.firebase_config import db

def create_maven_company():
    """Create the Maven company with custom onboarding steps"""
    print("Creating Maven company with custom onboarding steps...")
    
    # Define the custom onboarding steps
    maven_steps = [
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Account setup",
            description="Initial account setup and configuration",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Payment Processed",
            description="Confirm payment has been processed successfully",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Account activation (payment - pricing tiers)",
            description="Activate account based on selected pricing tier",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Build your AI team (meeting)",
            description="Initial meeting to discuss AI team composition",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Security & Compliance Setup",
            description="Guide on security protocols, data privacy, and admin controls",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Data integration",
            description="Connect and integrate your data sources",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Training the AI",
            description="Initial AI training with your data",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Schedule your first training session",
            description="Meet your team and schedule initial training",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Tutorial book / deployment period (two weeks)",
            description="Initial deployment with tutorial materials",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Share your thoughts about the AI agents",
            description="Provide feedback on initial AI performance",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Your AI team just got better (from junior to senior)",
            description="AI model improvements based on feedback",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Deployment period (two weeks)",
            description="Extended deployment period with monitoring",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Share your thoughts about the AI agents",
            description="Second round of feedback on AI performance",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Deployment period (two weeks)",
            description="Final deployment period with adjustments",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Handoff email (support email/chat etc)",
            description="Transition to ongoing support channels",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Performance reports",
            description="Review of AI performance metrics",
            status=OnboardingStatus.TODO
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Trial expiration / upgrade reminders",
            description="Notifications about trial status and upgrade options",
            status=OnboardingStatus.TODO
        )
    ]
    
    # Create company data
    company_data = {
        'name': 'Maven',
        'onboarding_steps': [step.to_dict() for step in maven_steps],
        'created_at': datetime.now().isoformat(),
        'user_ids': []  # Will be populated with user IDs later
    }
    
    # Add to Firestore
    try:
        company_ref = db.collection('companies').document()
        company_ref.set(company_data)
        company_id = company_ref.id
        print(f"✅ Successfully created Maven company with ID: {company_id}")
        return company_id
    except Exception as e:
        print(f"❌ Error creating Maven company: {e}")
        return None

def assign_user_to_maven(company_id, user_email):
    """Assign a user to the Maven company"""
    if not company_id:
        print("❌ Cannot assign user: Company ID is missing")
        return False
        
    try:
        # Find user by email
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', user_email).limit(1)
        user_docs = list(query.stream())
        
        if not user_docs:
            print(f"❌ User with email {user_email} not found")
            return False
            
        user_id = user_docs[0].id
        user_data = user_docs[0].to_dict()
        
        # Update user's company_ids
        company_ids = user_data.get('company_ids', [])
        if company_id not in company_ids:
            company_ids.append(company_id)
            users_ref.document(user_id).update({'company_ids': company_ids})
        
        # Update company's user_ids
        company_ref = db.collection('companies').document(company_id)
        company_data = company_ref.get().to_dict()
        user_ids = company_data.get('user_ids', [])
        if user_id not in user_ids:
            user_ids.append(user_id)
            company_ref.update({'user_ids': user_ids})
        
        print(f"✅ Successfully assigned user {user_email} to Maven company")
        return True
    except Exception as e:
        print(f"❌ Error assigning user to Maven company: {e}")
        return False

def main():
    """Main function to create Maven company and assign users"""
    print("\n=== Creating Maven Company ===\n")
    
    # Create the Maven company
    company_id = create_maven_company()
    
    if company_id:
        # Ask if user wants to assign a user to the company
        assign_user = input("\nDo you want to assign a user to the Maven company? (y/n): ").strip().lower()
        if assign_user == 'y':
            user_email = input("Enter the user's email: ").strip()
            assign_user_to_maven(company_id, user_email)
    
    print("\n=== Maven Company Setup Complete ===\n")

if __name__ == "__main__":
    main() 