#!/usr/bin/env python3
import os
import sys
import json
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def direct_update_agents():
    """Directly update Maven company's AI agents to 'ready' status"""
    print("\n=== DIRECT UPDATE OF MAVEN AI AGENTS ===\n")
    
    # The Maven company ID
    MAVEN_COMPANY_ID = "BE93DWq1pTotszXIhSOE"
    
    # Check if Firebase app is already initialized
    if not firebase_admin._apps:
        # Find the Firebase service account key
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        service_account_path = os.path.join(project_dir, 'firebase-sa-key.json')
        
        if not os.path.exists(service_account_path):
            print(f"❌ Firebase service account key not found at: {service_account_path}")
            return False
        
        # Initialize Firebase with service account
        print("Initializing Firebase...")
        try:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Firebase: {e}")
            return False
    
    # Get Firestore database
    db = firestore.client()
    
    # Define the sample AI agents in 'ready' status
    ai_agents = [
        {
            "name": "Proposal Analyst",
            "purpose": "Accepts RFI text documents as input and returns Proposal excel sheets as output",
            "status": "ready",
            "output": "https://storage.googleapis.com/synthetic-teams/output/proposal_output.xlsx",
            "input": "https://storage.googleapis.com/synthetic-teams/input/rfi_document.pdf",
            "training_time": 7
        },
        {
            "name": "Specbook Specialist",
            "purpose": "Accepts a spec from a client, turns it into a submittal log and submittal file",
            "status": "ready",
            "output": "https://storage.googleapis.com/synthetic-teams/output/submittal_log.xlsx",
            "input": "https://storage.googleapis.com/synthetic-teams/input/client_spec.pdf",
            "training_time": 5
        },
        {
            "name": "Form Processor",
            "purpose": "Makes sure the on-site team fills out all of the required forms every day",
            "status": "ready",
            "output": "https://storage.googleapis.com/synthetic-teams/output/daily_forms.pdf",
            "input": "https://storage.googleapis.com/synthetic-teams/input/form_template.docx",
            "training_time": 3
        }
    ]
    
    try:
        # Update the Maven company document
        company_ref = db.collection('companies').document(MAVEN_COMPANY_ID)
        company_ref.update({
            'aiagents': ai_agents,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        print(f"✅ Successfully updated Maven company with {len(ai_agents)} 'ready' AI agents")
        return True
    except Exception as e:
        print(f"❌ Error updating Maven company: {e}")
        return False
    finally:
        print("\n=== DIRECT UPDATE COMPLETE ===\n")

if __name__ == "__main__":
    direct_update_agents() 