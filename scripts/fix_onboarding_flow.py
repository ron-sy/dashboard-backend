#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime, timezone

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.firebase_config import db
from firebase_admin import firestore

def fix_onboarding_flow():
    """Comprehensive fix for the onboarding flow to ensure consistency"""
    print("\n=== FIXING ONBOARDING FLOW ===\n")
    
    company_id = "BE93DWq1pTotszXIhSOE"
    print(f"Working with company ID: {company_id}")
    
    company_ref = db.collection('companies').document(company_id)
    company_doc = company_ref.get()
    
    if not company_doc.exists:
        print(f"❌ Company with ID {company_id} not found")
        return False
    
    # Step 1: Delete the onboarding_steps array from the main document
    # This removes the duplication and ensures only one source of truth
    print("Step 1: Removing onboarding_steps from main document...")
    company_ref.update({'onboarding_steps': firestore.DELETE_FIELD})
    print("✅ Removed onboarding_steps array from main document")
    
    # Step 2: Delete all existing steps in the subcollection
    print("\nStep 2: Clearing existing onboarding subcollection...")
    batch = db.batch()
    steps_ref = company_ref.collection('onboarding')
    steps = list(steps_ref.stream())
    
    for step in steps:
        batch.delete(step.reference)
    
    batch.commit()
    print(f"✅ Deleted {len(steps)} existing steps")
    
    # Step 3: Create new steps with clear, consistent data structure
    print("\nStep 3: Creating new onboarding steps with consistent structure...")
    
    # Define the steps with proper data
    new_steps = [
        {
            'id': 'setup_account',
            'name': 'Account Setup',
            'description': 'Complete initial account setup and configuration',
            'status': 'done',
            'updated_at': firestore.SERVER_TIMESTAMP,
            # No todoLink or buttonText for completed steps without actions
        },
        {
            'id': 'process_payment',
            'name': 'Billing Setup',
            'description': 'Configure billing and payment settings',
            'status': 'done',
            'updated_at': firestore.SERVER_TIMESTAMP,
            'todoLink': '/billing',
            'buttonText': 'Billing'
        },
        {
            'id': 'data_integration',
            'name': 'Data Integration',
            'description': 'Connect and integrate your company data',
            'status': 'todo',
            'updated_at': firestore.SERVER_TIMESTAMP,
            'todoLink': f'/companies/{company_id}/data-sharing',
            'buttonText': 'Data Integration'
        },
        {
            'id': 'refer_friend',
            'name': 'Referrals',
            'description': 'Share Synthetic Teams with your network',
            'status': 'todo',
            'updated_at': firestore.SERVER_TIMESTAMP,
            'todoLink': '/referrals',
            'buttonText': 'Referrals'
        },
        {
            'id': 'ai_agents',
            'name': 'AI Agents',
            'description': 'Configure and deploy your AI agents',
            'status': 'todo',
            'updated_at': firestore.SERVER_TIMESTAMP,
            'todoLink': f'/companies/{company_id}/ai-agents',
            'buttonText': 'AI Agents'
        },
        {
            'id': 'training_session',
            'name': 'Training Session',
            'description': 'Schedule a training session with our team',
            'status': 'todo',
            'updated_at': firestore.SERVER_TIMESTAMP,
            # No redirect for this step
        },
        {
            'id': 'performance_review',
            'name': 'Performance Review',
            'description': 'Review AI agent performance and metrics',
            'status': 'todo',
            'updated_at': firestore.SERVER_TIMESTAMP,
            # No redirect for this step
        }
    ]
    
    # Create steps in the subcollection
    batch = db.batch()
    for step in new_steps:
        step_id = step.pop('id')  # Remove id from the data dict
        step_ref = steps_ref.document(step_id)
        batch.set(step_ref, step)
        
    batch.commit()
    print(f"✅ Created {len(new_steps)} new onboarding steps with consistent structure")
    
    print("\n=== ONBOARDING FLOW FIXED ===\n")
    return True

if __name__ == "__main__":
    fix_onboarding_flow() 