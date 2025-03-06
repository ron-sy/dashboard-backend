import os
import sys
from datetime import datetime, timezone

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.firebase_config import db

def update_maven_company():
    """Update Maven company with expanded structure"""
    print("Updating Maven company with expanded structure...")
    
    # Maven company ID
    maven_id = "w5SqiJlHiXjTO3jFIy7t"
    
    # Get current company data
    company_ref = db.collection('companies').document(maven_id)
    company_doc = company_ref.get()
    
    if not company_doc.exists:
        print(f"❌ Maven company with ID {maven_id} not found")
        return False
    
    current_data = company_doc.to_dict()
    
    # Prepare the expanded company data
    expanded_data = {
        'id': maven_id,
        'name': current_data.get('name', 'Maven'),
        'created_at': current_data.get('created_at'),
        'team_members': [
            {
                'user_id': 'JlPSlu0kPiNChXc0AY2q7t3ZUt02',
                'role': 'owner',
                'joined_at': '2025-02-27T10:11:02.871810'
            },
            {
                'user_id': 'z24a90kubBYlKzgXQX8lgx47job2',
                'role': 'admin',
                'joined_at': '2025-02-27T10:15:00.000000'
            },
            {
                'user_id': '1wjYMOXarVMs7KXDtrFDPn1jxM52',
                'role': 'member',
                'joined_at': '2025-02-27T10:20:00.000000'
            },
            {
                'user_id': 'G6yGrbfTo5YDRDqWO90kuP8eTkB3',
                'role': 'member',
                'joined_at': '2025-02-27T10:25:00.000000'
            }
        ],
        'data_sharing': {
            'is_connected': True,
            'connection_type': 'google_drive',
            'connected_at': '2025-02-27T11:00:00.000000',
            'connection_details': {
                'source_name': 'Maven Team Drive',
                'source_id': 'drive_maven_2025'
            }
        },
        'output_library': {
            'files': [
                {
                    'id': 'file_001',
                    'name': 'Q1 2025 Analysis.pdf',
                    'description': 'First quarter analysis report for Maven',
                    'file_type': 'pdf',
                    'download_url': 'https://storage.synthetic.teams/maven/q1_2025_analysis.pdf',
                    'size_bytes': 2048576,
                    'uploaded_at': '2025-03-01T09:00:00.000000',
                    'uploaded_by': 'JlPSlu0kPiNChXc0AY2q7t3ZUt02'
                },
                {
                    'id': 'file_002',
                    'name': 'Team Structure.docx',
                    'description': 'Maven team organization and roles',
                    'file_type': 'docx',
                    'download_url': 'https://storage.synthetic.teams/maven/team_structure.docx',
                    'size_bytes': 1048576,
                    'uploaded_at': '2025-03-02T14:30:00.000000',
                    'uploaded_by': 'z24a90kubBYlKzgXQX8lgx47job2'
                }
            ],
            'total_files': 2,
            'total_size_bytes': 3097152
        },
        # Preserve existing fields
        'user_ids': current_data.get('user_ids', []),
        'onboarding_steps': current_data.get('onboarding_steps', [])
    }
    
    # Update in Firestore
    try:
        company_ref.update(expanded_data)
        print(f"✅ Successfully updated Maven company with expanded structure")
        return True
    except Exception as e:
        print(f"❌ Error updating Maven company: {e}")
        return False

if __name__ == "__main__":
    update_maven_company() 