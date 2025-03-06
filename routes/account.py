from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
import pytz
from .auth import require_auth
import json

account_bp = Blueprint('account', __name__)
db = firestore.client()

@account_bp.route('/api/account/profile', methods=['GET'])
@require_auth
def get_profile(current_user):
    """Get user profile information."""
    try:
        print("Current user from auth:", json.dumps(current_user, indent=2))
        
        # Get the user's document from Firestore
        user_ref = db.collection('users').document(current_user['uid'])
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            print(f"User document not found for uid: {current_user['uid']}")
            return jsonify({'error': 'User profile not found'}), 404
            
        user_data = user_doc.to_dict()
        print("Raw Firestore user data:", json.dumps(user_data, indent=2, default=str))
        
        # Return the profile data in the expected format
        profile_data = {
            "display_name": user_data.get('display_name'),
            "email": user_data.get('email'),
            "role": user_data.get('role'),
            "profile": user_data.get('profile', {}),  # Get the entire profile object as is
            "referrals": user_data.get('referrals', {
                'referral_count': 0,
                'referred_emails': [],
                'last_referral_date': None
            })
        }
        
        print("Formatted profile data:", json.dumps(profile_data, indent=2, default=str))
        return jsonify(profile_data), 200
        
    except Exception as e:
        print(f"Error in get_profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@account_bp.route('/api/account/profile', methods=['PATCH'])
@require_auth
def update_profile(current_user):
    """Update user profile information."""
    try:
        # Get the update data from request
        update_data = request.get_json()
        print("Update data received:", json.dumps(update_data, indent=2))
        
        # Get user reference
        user_ref = db.collection('users').document(current_user['uid'])
        
        # Update the profile in Firestore
        user_ref.set(update_data, merge=True)
        
        # Get and return the updated data
        updated_doc = user_ref.get()
        updated_data = updated_doc.to_dict()
        
        # Format the response data
        formatted_data = {
            "display_name": updated_data.get('display_name'),
            "email": updated_data.get('email'),
            "role": updated_data.get('role'),
            "profile": updated_data.get('profile', {}),
            "referrals": updated_data.get('referrals', {
                'referral_count': 0,
                'referred_emails': [],
                'last_referral_date': None
            })
        }
        
        print("Updated profile:", json.dumps(formatted_data, indent=2, default=str))
        return jsonify(formatted_data), 200
        
    except Exception as e:
        print(f"Error in update_profile: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500 