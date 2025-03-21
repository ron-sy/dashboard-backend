#!/usr/bin/env python3
import os
import sys
from datetime import datetime, timezone

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.firebase_config import db
from firebase_admin import firestore

def update_ai_agents():
    """Update AI agents for Maven company to have 'ready' status instead of 'training'"""
    print("\n=== UPDATING AI AGENT STATUS FOR MAVEN ===\n")
    
    # Maven company ID
    company_id = "BE93DWq1pTotszXIhSOE"
    
    # Get the Maven company document
    company_ref = db.collection('companies').document(company_id)
    company_doc = company_ref.get()
    
    if not company_doc.exists:
        print(f"❌ Maven company with ID {company_id} not found")
        return False
    
    company_data = company_doc.to_dict()
    
    # Get current AI agents
    ai_agents = company_data.get('aiagents', [])
    if not ai_agents:
        print(f"No AI agents found for Maven company")
        return False
    
    # Update all agents with 'training' status to 'ready'
    updated_agents = []
    count = 0
    for agent in ai_agents:
        if agent.get('status') == 'training':
            agent['status'] = 'ready'
            print(f"Updating agent '{agent.get('name')}' status to 'ready'")
            count += 1
        updated_agents.append(agent)
    
    # Update the company document
    if count > 0:
        company_ref.update({
            'aiagents': updated_agents,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        print(f"✅ Updated {count} agents for Maven company")
    else:
        print("No training agents found to update")
    
    print("\n=== AI AGENT STATUS UPDATE COMPLETE ===\n")
    return count

if __name__ == "__main__":
    update_ai_agents() 