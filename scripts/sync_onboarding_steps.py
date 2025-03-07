#!/usr/bin/env python3
import os
import sys
import json
from datetime import datetime, timezone

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.firebase_config import db
from firebase_admin import firestore
from src.models import OnboardingStep, OnboardingStatus

def sync_onboarding_steps(company_id=None):
    """Sync onboarding steps between company document and subcollection."""
    print("\n=== SYNCING ONBOARDING STEPS ===\n")
    
    if company_id:
        company_ids = [company_id]
    else:
        # Get all companies if no specific ID provided
        companies_ref = db.collection('companies')
        companies = list(companies_ref.stream())
        company_ids = [doc.id for doc in companies]
    
    for company_id in company_ids:
        print(f"Processing company: {company_id}")
        company_ref = db.collection('companies').document(company_id)
        company_doc = company_ref.get()
        
        if not company_doc.exists:
            print(f"❌ Company with ID {company_id} not found")
            continue
        
        company_data = company_doc.to_dict()
        
        # Get steps from subcollection
        onboarding_ref = company_ref.collection('onboarding')
        steps_docs = list(onboarding_ref.stream())
        
        if not steps_docs:
            print(f"No steps in subcollection for company {company_id}")
            
            # If no steps in subcollection but steps in main document, create them in subcollection
            if 'onboarding_steps' in company_data and company_data['onboarding_steps']:
                print(f"Found {len(company_data['onboarding_steps'])} steps in company document. Creating in subcollection...")
                
                for step_data in company_data['onboarding_steps']:
                    # Convert timestamp to string if needed
                    if 'updated_at' in step_data and isinstance(step_data['updated_at'], datetime):
                        step_data['updated_at'] = step_data['updated_at'].isoformat()
                    
                    # Use existing ID if present, otherwise generate document ID
                    step_id = step_data.get('id')
                    if step_id:
                        onboarding_ref.document(step_id).set(step_data)
                    else:
                        # Create a new document with auto-generated ID
                        onboarding_ref.add(step_data)
                
                print(f"✅ Created {len(company_data['onboarding_steps'])} steps in subcollection")
            else:
                print(f"No steps found in company document either. Skipping.")
                continue
        else:
            # Steps found in subcollection, update the main document
            print(f"Found {len(steps_docs)} steps in subcollection. Updating company document...")
            
            steps_array = []
            for doc in steps_docs:
                step_data = doc.to_dict()
                step_data['id'] = doc.id
                steps_array.append(step_data)
            
            company_ref.update({'onboarding_steps': steps_array})
            print(f"✅ Updated company document with {len(steps_array)} steps from subcollection")
        
        print(f"✅ Successfully synced onboarding steps for company {company_id}")
        print("---")
    
    print("\n=== SYNC COMPLETED ===\n")
    return True

if __name__ == "__main__":
    # Check if company ID was provided as command line argument
    company_id = sys.argv[1] if len(sys.argv) > 1 else None
    sync_onboarding_steps(company_id) 