#!/usr/bin/env python3
import os
import json
from datetime import datetime

def create_ready_agents():
    """Create a JSON file with AI agents in 'ready' status for demonstration"""
    print("\n=== CREATING READY AI AGENTS SAMPLE ===\n")
    
    # Sample AI agents with 'ready' status
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
    
    # Create a directory for the output if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Write the AI agents to a JSON file
    output_file = os.path.join(output_dir, 'ready_agents.json')
    with open(output_file, 'w') as f:
        json.dump(ai_agents, f, indent=2)
    
    print(f"✅ Created sample AI agents with 'ready' status")
    print(f"✅ Output file: {output_file}")
    
    # Print instructions for integration
    print("\n=== INTEGRATION INSTRUCTIONS ===")
    print("To use these AI agents:")
    print("1. Copy the JSON content from the output file")
    print("2. In the Firebase console, navigate to the Maven company document")
    print("3. Update the 'aiagents' field with this JSON array")
    print("4. Or use the Firebase Admin SDK in the console to update the document")
    
    # Print the JSON for easy copying
    print("\n=== SAMPLE JSON FOR COPY/PASTE ===")
    print(json.dumps(ai_agents, indent=2))
    print("\n=== SAMPLE CREATION COMPLETE ===\n")
    
    return output_file

if __name__ == "__main__":
    create_ready_agents() 