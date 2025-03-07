#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.firebase_config import db
from firebase_admin import firestore

def update_maven_onboarding():
    """Update Maven onboarding steps with proper redirects and button texts"""
    print("\n=== UPDATING MAVEN ONBOARDING STEPS ===\n")
    
    company_id = "BE93DWq1pTotszXIhSOE"
    company_ref = db.collection('companies').document(company_id)
    company_doc = company_ref.get()
    
    if not company_doc.exists:
        print(f"❌ Maven company with ID {company_id} not found")
        return False
    
    # Get onboarding subcollection reference
    onboarding_ref = company_ref.collection('onboarding')
    
    # Delete existing onboarding steps
    print("Deleting existing onboarding steps...")
    batch = db.batch()
    docs = list(onboarding_ref.stream())
    for doc in docs:
        batch.delete(doc.reference)
    batch.commit()
    print(f"✅ Deleted {len(docs)} existing onboarding steps")
    
    # Create new onboarding steps
    print("\nCreating new onboarding steps...")
    
    # Step 1: Setup Account (completed)
    setup_account_ref = onboarding_ref.document('setup_account')
    setup_account = {
        'name': 'Account Setup',
        'description': 'Complete initial account setup and configuration',
        'status': 'done',
        'updated_at': firestore.SERVER_TIMESTAMP,
    }
    setup_account_ref.set(setup_account)
    print("✅ Created 'Account Setup' step")
    
    # Step 2: Process Payment (completed)
    process_payment_ref = onboarding_ref.document('process_payment')
    process_payment = {
        'name': 'Payment Processing',
        'description': 'Complete the initial payment for onboarding',
        'status': 'done',
        'updated_at': firestore.SERVER_TIMESTAMP,
        'todoLink': '/billing',
        'buttonText': 'Go to Billing'
    }
    process_payment_ref.set(process_payment)
    print("✅ Created 'Payment Processing' step")
    
    # Step 3: Data Integration
    data_integration_ref = onboarding_ref.document('data_integration')
    data_integration = {
        'name': 'Data Integration',
        'description': 'Connect and integrate your company data',
        'status': 'todo',
        'updated_at': firestore.SERVER_TIMESTAMP,
        'todoLink': '/companies/BE93DWq1pTotszXIhSOE/data-sharing',
        'buttonText': 'Go to Data Integration'
    }
    data_integration_ref.set(data_integration)
    print("✅ Created 'Data Integration' step")
    
    # Step 4: Refer a Friend
    refer_friend_ref = onboarding_ref.document('refer_friend')
    refer_friend = {
        'name': 'Refer a Friend',
        'description': 'Share Synthetic Teams with your network',
        'status': 'todo',
        'updated_at': firestore.SERVER_TIMESTAMP,
        'todoLink': '/referrals',
        'buttonText': 'Go to Referrals'
    }
    refer_friend_ref.set(refer_friend)
    print("✅ Created 'Refer a Friend' step")
    
    # Step 5: AI Agents
    ai_agents_ref = onboarding_ref.document('ai_agents')
    ai_agents = {
        'name': 'AI Agents',
        'description': 'Configure and deploy your AI agents',
        'status': 'todo',
        'updated_at': firestore.SERVER_TIMESTAMP,
        'todoLink': '/companies/BE93DWq1pTotszXIhSOE/ai-agents',
        'buttonText': 'Go to AI Agents'
    }
    ai_agents_ref.set(ai_agents)
    print("✅ Created 'AI Agents' step")
    
    # Step 6: Training Session (no redirect link)
    training_ref = onboarding_ref.document('training_session')
    training = {
        'name': 'Training Session',
        'description': 'Schedule a training session with our team',
        'status': 'todo',
        'updated_at': firestore.SERVER_TIMESTAMP
        # No todoLink or buttonText for this step
    }
    training_ref.set(training)
    print("✅ Created 'Training Session' step (no redirect)")
    
    # Step 7: Performance Review (no redirect link)
    review_ref = onboarding_ref.document('performance_review')
    review = {
        'name': 'Performance Review',
        'description': 'Review AI agent performance and metrics',
        'status': 'todo',
        'updated_at': firestore.SERVER_TIMESTAMP
        # No todoLink or buttonText for this step
    }
    review_ref.set(review)
    print("✅ Created 'Performance Review' step (no redirect)")
    
    print("\n✅ Successfully updated all onboarding steps")
    return True

if __name__ == "__main__":
    update_maven_onboarding() 