#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.firebase_config import db
from firebase_admin import firestore

def enable_platform_access():
    """Enable platform access for the Maven company."""
    print("\n=== ENABLING PLATFORM ACCESS ===\n")
    
    company_id = "BE93DWq1pTotszXIhSOE"  # Maven company ID
    company_ref = db.collection('companies').document(company_id)
    company_doc = company_ref.get()
    
    if not company_doc.exists:
        print(f"❌ Company with ID {company_id} not found")
        return False
    
    # Update the company document to enable platform access
    company_ref.update({
        'platform_access': True,
        'platform_enabled_at': firestore.SERVER_TIMESTAMP
    })
    
    print(f"✅ Platform access enabled for company: {company_doc.get('name')}")
    print(f"✅ Company ID: {company_id}")
    print("\n=== PLATFORM ACCESS ENABLED ===\n")
    return True

if __name__ == "__main__":
    enable_platform_access() 