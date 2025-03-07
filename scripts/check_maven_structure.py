#!/usr/bin/env python3
import os
import sys
import json

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.firebase_config import db

def check_maven_structure():
    """Check the structure of the Maven company with ID BE93DWq1pTotszXIhSOE"""
    print("\n=== CHECKING MAVEN COMPANY STRUCTURE ===\n")
    
    company_id = "BE93DWq1pTotszXIhSOE"
    company_ref = db.collection('companies').document(company_id)
    company_doc = company_ref.get()
    
    if not company_doc.exists:
        print(f"❌ Maven company with ID {company_id} not found")
        return
    
    company_data = company_doc.to_dict()
    print(f"✅ Found Maven company with name: {company_data.get('name', 'Unknown')}")
    
    # Check onboarding steps
    print("\n=== ONBOARDING STEPS ===")
    if 'onboarding_steps' in company_data:
        steps = company_data['onboarding_steps']
        print(f"Found {len(steps)} steps in company document:")
        for i, step in enumerate(steps):
            print(f"{i+1}. {step.get('name', 'Unnamed')} - Status: {step.get('status', 'Unknown')}")
            print(f"   Description: {step.get('description', 'No description')}")
            if 'todoLink' in step:
                print(f"   Redirect Link: {step.get('todoLink', 'None')}")
            if 'buttonText' in step:
                print(f"   Button Text: {step.get('buttonText', 'None')}")
            print("")
    else:
        print("No onboarding steps found in company document")
    
    # Check onboarding subcollection
    print("\n=== ONBOARDING SUBCOLLECTION ===")
    onboarding_ref = company_ref.collection('onboarding')
    onboarding_docs = list(onboarding_ref.stream())
    
    if onboarding_docs:
        print(f"Found {len(onboarding_docs)} documents in onboarding subcollection:")
        for i, doc in enumerate(onboarding_docs):
            step_data = doc.to_dict()
            print(f"{i+1}. {doc.id}: {step_data.get('name', 'Unnamed')} - Status: {step_data.get('status', 'Unknown')}")
            print(f"   Description: {step_data.get('description', 'No description')}")
            if 'todoLink' in step_data:
                print(f"   Redirect Link: {step_data.get('todoLink', 'None')}")
            if 'buttonText' in step_data:
                print(f"   Button Text: {step_data.get('buttonText', 'None')}")
            print("")
    else:
        print("No documents found in onboarding subcollection")
        
    print("\n=== STRUCTURE CHECK COMPLETE ===\n")

if __name__ == "__main__":
    check_maven_structure() 