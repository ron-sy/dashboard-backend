#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.firebase_config import db
from firebase_admin import firestore

def update_button_texts():
    """Update the button texts for the Maven company to be more descriptive"""
    print("\n=== UPDATING BUTTON TEXTS ===\n")
    
    company_id = "BE93DWq1pTotszXIhSOE"
    company_ref = db.collection('companies').document(company_id)
    company_doc = company_ref.get()
    
    if not company_doc.exists:
        print(f"❌ Maven company with ID {company_id} not found")
        return False
    
    # Define the new button texts
    button_updates = {
        'refer_friend': {
            'buttonText': 'Referrals'
        },
        'data_integration': {
            'buttonText': 'Data Integration'
        },
        'process_payment': {
            'buttonText': 'Billing'
        },
        'ai_agents': {
            'buttonText': 'AI Agents'
        }
    }
    
    # Update the steps in the subcollection
    for step_id, updates in button_updates.items():
        step_ref = company_ref.collection('onboarding').document(step_id)
        step_doc = step_ref.get()
        
        if not step_doc.exists:
            print(f"❌ Step {step_id} not found")
            continue
        
        step_ref.update(updates)
        print(f"✅ Updated {step_id} button text to '{updates['buttonText']}'")
    
    # Now run the sync script to update the main document
    from scripts.sync_onboarding_steps import sync_onboarding_steps
    sync_onboarding_steps(company_id)
    
    print("\n=== BUTTON TEXTS UPDATED ===\n")
    return True

if __name__ == "__main__":
    update_button_texts() 