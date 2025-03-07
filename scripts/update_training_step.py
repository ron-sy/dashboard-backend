#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.firebase_config import db
from firebase_admin import firestore

def update_training_step():
    """Update the training_session step with a Calendly link"""
    print("\n=== UPDATING TRAINING SESSION STEP ===\n")
    
    company_id = "BE93DWq1pTotszXIhSOE"
    print(f"Working with company ID: {company_id}")
    
    company_ref = db.collection('companies').document(company_id)
    company_doc = company_ref.get()
    
    if not company_doc.exists:
        print(f"❌ Company with ID {company_id} not found")
        return False
    
    # Get the training_session step
    step_ref = company_ref.collection('onboarding').document('training_session')
    step_doc = step_ref.get()
    
    if not step_doc.exists:
        print(f"❌ Training session step not found")
        return False
    
    # Update the step with Calendly link
    step_data = step_doc.to_dict()
    step_data.update({
        'todoLink': 'https://calendly.com/ron-syntheticteams',
        'buttonText': 'Schedule Training',
        'updated_at': firestore.SERVER_TIMESTAMP
    })
    
    # Write back to Firestore
    step_ref.update(step_data)
    print(f"✅ Updated training_session step with Calendly link")
    
    print("\n=== UPDATE COMPLETE ===\n")
    return True

if __name__ == "__main__":
    update_training_step() 