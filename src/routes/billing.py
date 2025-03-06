from flask import Blueprint, request, jsonify
from firebase_admin import firestore
from datetime import datetime
import pytz
from .auth import require_auth
import json

billing_bp = Blueprint('billing', __name__)
db = firestore.client()

@billing_bp.route('/api/billing/info', methods=['GET'])
@require_auth
def get_billing_info(current_user):
    """Get user billing information."""
    try:
        print("Current user from auth:", json.dumps(current_user, indent=2))
        
        # Get the user's document from Firestore
        user_ref = db.collection('users').document(current_user['uid'])
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            print(f"User document not found for uid: {current_user['uid']}")
            return jsonify({'error': 'User billing info not found'}), 404
            
        user_data = user_doc.to_dict()
        print("Raw Firestore user data:", json.dumps(user_data, indent=2, default=str))
        
        # Get billing info from user data
        billing_data = {
            "billing": user_data.get('billing', {
                'form_of_payment': None,
                'payment_transferred': 0,
                'payment_due': 0,
                'payment_remaining': 0,
                'payment_history': []
            })
        }
        
        print("Formatted billing data:", json.dumps(billing_data, indent=2, default=str))
        return jsonify(billing_data), 200
        
    except Exception as e:
        print(f"Error in get_billing_info: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@billing_bp.route('/api/billing/info', methods=['PATCH'])
@require_auth
def update_billing_info(current_user):
    """Update user billing information."""
    try:
        # Get the update data from request
        update_data = request.get_json()
        print("Update data received:", json.dumps(update_data, indent=2))
        
        # Get user reference
        user_ref = db.collection('users').document(current_user['uid'])
        
        # Update the billing info in Firestore
        user_ref.set({'billing': update_data}, merge=True)
        
        # Get and return the updated data
        updated_doc = user_ref.get()
        updated_data = updated_doc.to_dict()
        
        # Format the response data
        formatted_data = {
            "billing": updated_data.get('billing', {
                'form_of_payment': None,
                'payment_transferred': 0,
                'payment_due': 0,
                'payment_remaining': 0,
                'payment_history': []
            })
        }
        
        print("Updated billing info:", json.dumps(formatted_data, indent=2, default=str))
        return jsonify(formatted_data), 200
        
    except Exception as e:
        print(f"Error in update_billing_info: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500 