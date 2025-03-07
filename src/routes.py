import sys
import os
from flask import Blueprint, request, jsonify
from firebase_admin import auth
import json
import uuid
from datetime import datetime, timedelta
import traceback
from firebase_admin import firestore

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config.firebase_config import db
from src.models import Company, OnboardingStep, OnboardingStatus, DEFAULT_ONBOARDING_STEPS
from src.models import User, UserRole
from typing import Dict, List, Any, Optional
from src.services import MandrillEmailService

# Create a Blueprint for API routes
api = Blueprint('api', __name__)

# Always use production Firebase, never use development mode
DEV_MODE = False

# Initialize Mandrill email service
mandrill_service = MandrillEmailService()

# Mock users for development mode
MOCK_USERS = {
    "admin@example.com": {
        "uid": "dev-admin-123",
        "role": "admin",
        "password": "Password123",
        "display_name": "Admin User",
        "email": "admin@example.com",
    },
    "john.doe@technova.com": {
        "uid": "dev-user-456",
        "password": "Password123",
        "display_name": "John Doe",
        "email": "john.doe@technova.com",
    },
    "sarah.smith@alpha.com": {
        "uid": "dev-user-789",
        "password": "Password123",
        "display_name": "Sarah Smith",
        "email": "sarah.smith@alpha.com",
    }
}

def create_empty_profile():
    """Create an empty profile with default fields."""
    return {
        'profile': {
            'firstName': '',
            'lastName': '',
            'phoneNumber': '',
            'avatar_url': None,
            'job_title': None,
            'department': None,
            'phone': None,
            'timezone': 'UTC',
            'language_preference': 'en',
            'business_address': {
                'street': None,
                'city': None,
                'state': None,
                'postal_code': None,
                'country': None
            },
            'notification_preferences': {
                'email_notifications': True,
                'desktop_notifications': True,
                'mobile_notifications': True,
                'notification_types': {
                    'team_updates': True,
                    'system_alerts': True,
                    'reports': True,
                    'mentions': True
                }
            },
            'system_preferences': {
                'theme': 'system',
                'date_format': 'MM/DD/YYYY',
                'time_format': '12h'
            },
            'security': {
                'two_factor_enabled': False,
                'last_password_change': datetime.now().isoformat(),
                'login_history': []
            }
        }
    }

def verify_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Verify Firebase ID token and return user info."""
    # In development mode, skip auth
    if DEV_MODE:
        print("DEV MODE: Skipping token verification")
        return {"uid": "dev-user-123", "email": "dev@example.com"}
    
    try:
        # First try to verify with Firebase Auth
        print(f"Verifying token: {id_token[:20]}...")
        decoded_token = auth.verify_id_token(id_token)
        print(f"Token verified. User info:", json.dumps(decoded_token, indent=2))
        
        # Check if user exists in Firestore, if not create them
        user_id = decoded_token.get('uid')
        user_email = decoded_token.get('email')
        print(f"Looking up user in Firestore - ID: {user_id}, Email: {user_email}")
        
        if user_id and user_email:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                print(f"Creating new user record in Firestore for: {user_email}")
                # Create a user record with empty profile fields
                user_data = {
                    'email': user_email,
                    'display_name': decoded_token.get('name', user_email.split('@')[0]),
                    'role': UserRole.USER,  # Default role
                    'company_ids': [],
                    'created_at': datetime.now().isoformat(),
                    **create_empty_profile()  # Add empty profile fields
                }
                user_ref.set(user_data)
            else:
                print(f"Found existing user in Firestore:", json.dumps(user_doc.to_dict(), indent=2, default=str))
        
        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        traceback.print_exc()
        return None

def get_user_from_token(auth_header: str) -> Optional[Dict[str, Any]]:
    """Extract and verify token from Authorization header"""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split('Bearer ')[1]
    return verify_token(token)

def get_user_data(user_id: str) -> Optional[User]:
    """Get a user's data from Firestore"""
    try:
        user_doc = db.collection('users').document(user_id).get()
        if not user_doc.exists:
            return None
        
        return User.from_dict(user_doc.to_dict(), user_id)
    except Exception as e:
        print(f"Error getting user data: {e}")
        return None

def is_admin(user_info: Dict[str, Any]) -> bool:
    """Check if the user is an admin"""
    # In dev mode, consider admin@example.com as admin
    if DEV_MODE and user_info.get('email') == 'admin@example.com':
        return True
    
    # Special case for specific admin email
    if user_info.get('email') == 'ronadin2002@gmail.com':
        # Ensure this user has admin role in Firestore
        user_id = user_info.get('uid')
        if user_id:
            try:
                user_ref = db.collection('users').document(user_id)
                user_doc = user_ref.get()
                
                if not user_doc.exists:
                    # Create admin user if doesn't exist
                    user_data = {
                        'email': 'ronadin2002@gmail.com',
                        'display_name': 'Admin',
                        'role': UserRole.ADMIN,
                        'company_ids': [],
                        'created_at': datetime.now().isoformat()
                    }
                    user_ref.set(user_data)
                else:
                    # Update to admin if not already
                    user_data = user_doc.to_dict()
                    if user_data.get('role') != UserRole.ADMIN:
                        user_ref.update({'role': UserRole.ADMIN})
            except Exception as e:
                print(f"Error ensuring admin status: {e}")
        
        return True
    
    # Check in Firestore
    user_id = user_info.get('uid')
    user = get_user_data(user_id)
    return user.is_admin if user else False

def check_company_access(user_id: str, company_id: str) -> bool:
    """Check if user has access to the company"""
    if DEV_MODE:
        return True  # All users have access to all companies in dev mode
    
    # Get user data
    user = get_user_data(user_id)
    if not user:
        return False
    
    # Admins have access to all companies
    if user.is_admin:
        return True
    
    # Check if company is in user's company_ids
    return company_id in user.company_ids

# Mock auth endpoint for development testing
@api.route('/dev-auth/login', methods=['POST'])
def dev_login():
    """Development-only endpoint for login testing"""
    if not DEV_MODE:
        return jsonify({'error': 'Endpoint only available in development mode'}), 403
    
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    email = data['email']
    password = data['password']
    
    if email in MOCK_USERS and MOCK_USERS[email]['password'] == password:
        user = MOCK_USERS[email]
        is_admin_user = email == 'admin@example.com'
        
        # Create or update the user in Firestore
        try:
            user_ref = db.collection('users').document(user['uid'])
            user_exists = user_ref.get().exists
            
            user_data = {
                'email': user['email'],
                'display_name': user['display_name'],
                'role': UserRole.ADMIN if is_admin_user else UserRole.USER,
                'created_at': datetime.now().isoformat()
            }
            
            if not user_exists:
                user_data['company_ids'] = []
                user_ref.set(user_data)
            else:
                user_ref.update(user_data)
        except Exception as e:
            print(f"Error storing mock user in Firestore: {e}")
        
        return jsonify({
            'uid': user['uid'],
            'email': user['email'],
            'displayName': user['display_name'],
            'idToken': f"mock-token-{user['uid']}",
            'dev_mode': True,
            'isAdmin': is_admin_user
        }), 200
    
    return jsonify({'error': 'Invalid email or password'}), 401

# ADMIN ROUTES
@api.route('/admin/users', methods=['GET'])
def get_users():
    """Admin only: Get all users"""
    auth_header = request.headers.get('Authorization')
    user_info = get_user_from_token(auth_header)
    
    if not user_info:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    # Check if the user is an admin
    if not is_admin(user_info):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    # Get all users from Firestore
    users = []
    try:
        for doc in db.collection('users').stream():
            user = User.from_dict(doc.to_dict(), doc.id)
            users.append({
                'id': user.id,
                'email': user.email,
                'display_name': user.display_name,
                'role': user.role,
                'company_ids': user.company_ids,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({'error': 'Error fetching users'}), 500
    
    return jsonify(users), 200

@api.route('/admin/users', methods=['POST'])
def create_user():
    """Admin only: Create a new user"""
    auth_header = request.headers.get('Authorization')
    user_info = get_user_from_token(auth_header)
    
    if not user_info:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    # Check if the user is an admin
    if not is_admin(user_info):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    # Get request data
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    
    email = data['email']
    password = data.get('password', 'ChangeMe123')  # Default password
    display_name = data.get('display_name', email.split('@')[0])
    role = data.get('role', UserRole.USER)
    company_ids = data.get('company_ids', [])
    
    try:
        # Always create user in Firebase Authentication
        print(f"Creating user in Firebase Authentication: {email}")
        try:
            # Attempt to create user in Firebase Authentication
            user_record = auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            uid = user_record.uid
            print(f"Created Firebase Auth user with ID: {uid}")
        except Exception as auth_error:
            print(f"Error creating Firebase Auth user: {auth_error}")
            error_message = str(auth_error)
            if "ALREADY_EXISTS" in error_message:
                return jsonify({'error': 'User with this email already exists'}), 409
            else:
                return jsonify({'error': f'Failed to create user in Firebase: {error_message}'}), 500
            
        # Create the user in Firestore with empty profile fields
        user_ref = db.collection('users').document(uid)
        user_data = {
            'email': email,
            'display_name': display_name,
            'role': role,
            'company_ids': company_ids,
            'created_at': datetime.now().isoformat(),
            **create_empty_profile()  # Add empty profile fields
        }
        user_ref.set(user_data)
        
        # Update company user lists
        for company_id in company_ids:
            company_ref = db.collection('companies').document(company_id)
            company_doc = company_ref.get()
            if company_doc.exists:
                company_data = company_doc.to_dict()
                user_ids = company_data.get('user_ids', [])
                if uid not in user_ids:
                    user_ids.append(uid)
                    company_ref.update({'user_ids': user_ids})
        
        # Return the created user
        response_data = {
            'id': uid,
            'email': email,
            'display_name': display_name,
            'role': role,
            'company_ids': company_ids,
            'created_at': datetime.now().isoformat(),
            **create_empty_profile()  # Include empty profile fields in response
        }
        return jsonify(response_data), 201
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({'error': str(e)}), 500

@api.route('/admin/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Admin only: Update a user's details"""
    auth_header = request.headers.get('Authorization')
    user_info = get_user_from_token(auth_header)
    
    if not user_info:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    # Check if the user is an admin
    if not is_admin(user_info):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    # Get request data
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Get current user data
    user_ref = db.collection('users').document(user_id)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404
    
    current_user_data = user_doc.to_dict()
    
    # Update fields
    update_data = {}
    
    if 'display_name' in data:
        update_data['display_name'] = data['display_name']
    
    if 'role' in data:
        update_data['role'] = data['role']
    
    if 'company_ids' in data:
        old_company_ids = current_user_data.get('company_ids', [])
        new_company_ids = data['company_ids']
        update_data['company_ids'] = new_company_ids
        
        # Update company user lists
        # Remove user from companies they're no longer part of
        for company_id in old_company_ids:
            if company_id not in new_company_ids:
                try:
                    company_ref = db.collection('companies').document(company_id)
                    company_doc = company_ref.get()
                    if company_doc.exists:
                        company_data = company_doc.to_dict()
                        user_ids = company_data.get('user_ids', [])
                        if user_id in user_ids:
                            user_ids.remove(user_id)
                            company_ref.update({'user_ids': user_ids})
                except Exception as e:
                    print(f"Error removing user from company {company_id}: {e}")
        
        # Add user to new companies
        for company_id in new_company_ids:
            if company_id not in old_company_ids:
                try:
                    company_ref = db.collection('companies').document(company_id)
                    company_doc = company_ref.get()
                    if company_doc.exists:
                        company_data = company_doc.to_dict()
                        user_ids = company_data.get('user_ids', [])
                        if user_id not in user_ids:
                            user_ids.append(user_id)
                            company_ref.update({'user_ids': user_ids})
                except Exception as e:
                    print(f"Error adding user to company {company_id}: {e}")
    
    # Update the user
    if update_data:
        try:
            user_ref.update(update_data)
            
            # Get updated user data
            updated_user_doc = user_ref.get()
            updated_user = User.from_dict(updated_user_doc.to_dict(), user_id)
            
            return jsonify({
                'id': updated_user.id,
                'email': updated_user.email,
                'display_name': updated_user.display_name,
                'role': updated_user.role,
                'company_ids': updated_user.company_ids,
                'created_at': updated_user.created_at.isoformat() if updated_user.created_at else None
            }), 200
            
        except Exception as e:
            print(f"Error updating user: {e}")
            return jsonify({'error': f'Error updating user: {str(e)}'}), 500
    else:
        return jsonify({'error': 'No valid fields to update'}), 400

@api.route('/admin/companies/<company_id>/users', methods=['GET'])
def get_company_users(company_id):
    """Admin or company manager: Get all users for a company"""
    auth_header = request.headers.get('Authorization')
    user_info = get_user_from_token(auth_header)
    
    if not user_info:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    # Check if user has access to the company
    user_id = user_info.get('uid')
    if not is_admin(user_info) and not check_company_access(user_id, company_id):
        return jsonify({'error': 'Unauthorized access to this company'}), 403
    
    # Check if company exists
    company_ref = db.collection('companies').document(company_id)
    company_doc = company_ref.get()
    
    if not company_doc.exists:
        return jsonify({'error': 'Company not found'}), 404
    
    company_data = company_doc.to_dict()
    user_ids = company_data.get('user_ids', [])
    
    # Get user data for each user ID
    users = []
    for uid in user_ids:
        try:
            user_doc = db.collection('users').document(uid).get()
            if user_doc.exists:
                user = User.from_dict(user_doc.to_dict(), uid)
                users.append({
                    'id': user.id,
                    'email': user.email,
                    'display_name': user.display_name,
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                })
        except Exception as e:
            print(f"Error fetching user {uid}: {e}")
    
    return jsonify(users), 200

# COMPANY ROUTES
@api.route('/companies', methods=['GET'])
def get_companies():
    """Get all companies the user has access to."""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization required'}), 401
        
        # Extract and verify token
        user_info = get_user_from_token(auth_header)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get user data including role and company assignments
        user_id = user_info.get('uid')
        user_data = get_user_data(user_id)
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
        
        # Admin users can see all companies
        if is_admin(user_info):
            print(f"Admin user {user_id} accessed all companies")
            companies_ref = db.collection('companies')
        else:
            # Regular users can only see companies they are assigned to
            print(f"User {user_id} accessing their assigned companies")
            company_ids = user_data.company_ids
            if not company_ids:
                return jsonify([]), 200
                
            # Create a query to get only the companies this user is assigned to
            companies_ref = db.collection('companies').where('__name__', 'in', company_ids)
        
        # Get all companies (or filtered set for regular users)
        companies = []
        company_docs = companies_ref.stream()
        
        for doc in company_docs:
            company_data = doc.to_dict()
            company_data['id'] = doc.id
            
            # Don't include onboarding steps in the list view for performance
            if 'onboarding_steps' in company_data:
                del company_data['onboarding_steps']
                
            companies.append(company_data)
        
        return jsonify(companies), 200
    
    except Exception as e:
        print(f"Error getting companies: {e}")
        return jsonify({'error': f'Error getting companies: {str(e)}'}), 500

@api.route('/companies/<company_id>', methods=['GET'])
def get_company(company_id):
    """Get a specific company's details."""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization required'}), 401
        
        # Extract and verify token
        user_info = get_user_from_token(auth_header)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Check if the user has access to this company
        user_id = user_info.get('uid')
        user_data = get_user_data(user_id)
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
            
        is_user_admin = is_admin(user_info)
        
        # Only allow access if user is admin or assigned to this company
        if not is_user_admin and company_id not in user_data.company_ids:
            print(f"User {user_id} denied access to company {company_id}")
            return jsonify({'error': 'Unauthorized access to this company'}), 403
        
        # Get company details
        company_ref = db.collection('companies').document(company_id)
        company_doc = company_ref.get()
        
        if not company_doc.exists:
            return jsonify({'error': 'Company not found'}), 404
        
        company_data = company_doc.to_dict()
        company = Company.from_dict(company_data, company_id)
        
        # Get onboarding steps from subcollection
        onboarding_steps = []
        steps_ref = company_ref.collection('onboarding')
        for step_doc in steps_ref.stream():
            step_data = step_doc.to_dict()
            step_data['id'] = step_doc.id  # Add document ID to the data
            onboarding_steps.append(step_data)
        
        # Prepare response object
        response = {
            'id': company.id,
            'name': company.name,
            'onboarding_steps': onboarding_steps,  # Use steps from subcollection
            'created_at': company.created_at.isoformat() if company.created_at else None,
            'user_ids': company.user_ids,
            'user_is_admin': is_user_admin,  # Include this flag for frontend to determine edit permissions
            'team_members': company.team_members,
            'data_sharing': company.data_sharing,
            'output_library': company.output_library,
            'aiagents': company_data.get('aiagents', [])  # Add aiagents field to response
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error fetching company: {e}")
        return jsonify({'error': f'Error fetching company data: {str(e)}'}), 500

@api.route('/companies/<company_id>/onboarding', methods=['GET'])
def get_onboarding_steps(company_id):
    """Get onboarding steps for a company."""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization required'}), 401
        
        # Extract and verify token
        user_info = get_user_from_token(auth_header)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Check if the user has access to this company
        user_id = user_info.get('uid')
        user_data = get_user_data(user_id)
        
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
            
        is_user_admin = is_admin(user_info)
        
        # Only allow access if user is admin or assigned to this company
        if not is_user_admin and company_id not in user_data.company_ids:
            print(f"User {user_id} denied access to company {company_id}")
            return jsonify({'error': 'Unauthorized access to this company'}), 403
        
        # Get onboarding steps from subcollection
        onboarding_steps = {}
        steps_ref = db.collection('companies').document(company_id).collection('onboarding')
        steps = steps_ref.stream()
        
        for step in steps:
            step_data = step.to_dict()
            step_data['id'] = step.id  # Add document ID to the data
            onboarding_steps[step.id] = step_data
        
        return jsonify(onboarding_steps), 200
        
    except Exception as e:
        print(f"Error fetching onboarding steps: {e}")
        traceback.print_exc()  # Print full traceback for debugging
        return jsonify({'error': f'Error fetching onboarding data: {str(e)}'}), 500

@api.route('/companies/<company_id>/onboarding/<step_id>', methods=['PUT'])
def update_onboarding_step(company_id, step_id):
    """Update the status of an onboarding step."""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization required'}), 401
        
        # Extract and verify token
        user_info = get_user_from_token(auth_header)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Only admins can update onboarding step status
        if not is_admin(user_info):
            print(f"User {user_info.get('uid')} denied permission to update step {step_id} for company {company_id}")
            return jsonify({'error': 'Admin privileges required to update onboarding steps'}), 403
        
        # Get request data
        data = request.get_json()
        if 'status' not in data:
            return jsonify({'error': 'Status field is required'}), 400
        
        # Check if email notification is requested
        send_email = data.get('send_email', False)
        template_name = data.get('template_name')
        recipient_emails = data.get('recipient_emails', [])
        
        # Log the request data for debugging
        print(f"Request data: {data}")
        print(f"Send email: {send_email}, Template: {template_name}, Recipients: {recipient_emails}")
        
        # Validate status
        try:
            new_status = OnboardingStatus(data['status'])
        except ValueError:
            return jsonify({'error': 'Invalid status value'}), 400
        
        # Get company reference
        company_ref = db.collection('companies').document(company_id)
        company_doc = company_ref.get()
        
        if not company_doc.exists:
            return jsonify({'error': 'Company not found'}), 404
        
        company_data = company_doc.to_dict()
        
        # First, update the step in the subcollection
        step_ref = company_ref.collection('onboarding').document(step_id)
        step_doc = step_ref.get()
        
        if not step_doc.exists:
            return jsonify({'error': 'Onboarding step not found'}), 404
            
        # Update step in subcollection
        step_data = step_doc.to_dict()
        step_data['status'] = new_status
        step_data['updated_at'] = firestore.SERVER_TIMESTAMP
        step_ref.update(step_data)
        
        # Next, also update the step in the main company document
        steps_array = company_data.get('onboarding_steps', [])
        updated_steps = []
        step_found = False
        
        for step in steps_array:
            if step.get('id') == step_id:
                step_found = True
                # Update the status
                step['status'] = new_status
                step['updated_at'] = datetime.now().isoformat()
            updated_steps.append(step)
        
        # If step wasn't found in the array, get it from subcollection and add it
        if not step_found:
            # Refresh step data after update
            step_doc = step_ref.get()
            step_data = step_doc.to_dict()
            step_data['id'] = step_id
            updated_steps.append(step_data)
        
        # Update the company document
        company_ref.update({'onboarding_steps': updated_steps})
        
        # Send email notification if requested
        email_warning = None
        recipients_count = 0
        
        if send_email and template_name:
            # Code to send email notifications...
            pass
        
        # Prepare the response
        response = {
            'success': True,
            'message': 'Onboarding step updated successfully'
        }
        
        if email_warning:
            response['email_warning'] = email_warning
        
        if recipients_count > 0:
            response['recipients_count'] = recipients_count
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error updating onboarding step: {e}")
        traceback.print_exc()
        return jsonify({'error': f'Error updating onboarding step: {str(e)}'}), 500

@api.route('/companies', methods=['POST'])
def create_company():
    """Create a new company with default onboarding steps."""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization required'}), 401
        
        # Extract and verify token
        user_info = get_user_from_token(auth_header)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Only admins can create companies
        if not is_admin(user_info):
            print(f"User {user_info.get('uid')} denied permission to create company")
            return jsonify({'error': 'Admin privileges required to create companies'}), 403
        
        # Get request data
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Company name is required'}), 400
        
        user_ids = data.get('user_ids', [])
        
        # Create new company with default steps
        new_company = Company(
            id='',  # Firestore will generate an ID
            name=data['name'],
            onboarding_steps=DEFAULT_ONBOARDING_STEPS.copy(),
            created_at=datetime.now(),
            user_ids=user_ids
        )
        
        # Add to Firestore
        company_ref = db.collection('companies').document()
        company_ref.set(new_company.to_dict())
        
        # Update the generated ID
        new_company.id = company_ref.id
        
        # Update user records to include this company
        for user_id in user_ids:
            try:
                user_ref = db.collection('users').document(user_id)
                user_doc = user_ref.get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    company_ids = user_data.get('company_ids', [])
                    if new_company.id not in company_ids:
                        company_ids.append(new_company.id)
                        user_ref.update({'company_ids': company_ids})
            except Exception as e:
                print(f"Error updating user {user_id} with new company: {e}")
        
        return jsonify({
            'id': new_company.id,
            'name': new_company.name,
            'onboarding_steps': [step.to_dict() for step in new_company.onboarding_steps],
            'created_at': new_company.created_at.isoformat() if new_company.created_at else None,
            'user_ids': new_company.user_ids
        }), 201
        
    except Exception as e:
        print(f"Error creating company: {e}")
        return jsonify({'error': f'Error creating company: {str(e)}'}), 500

# New API endpoint to create an invitation
@api.route('/invitations', methods=['POST'])
def create_invitation():
    """Create a new invitation for a company."""
    # Get the authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Authorization header is required"}), 401
    
    # Verify the token and get user info
    user_info = get_user_from_token(auth_header)
    if not user_info:
        return jsonify({"error": "Invalid or expired token"}), 401
    
    # Check if user is an admin
    if not is_admin(user_info):
        return jsonify({"error": "Admin privileges required"}), 403
    
    # Get the request data
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    # Validate required fields
    required_fields = ['code', 'companyId', 'companyName', 'expiryDate']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Parse expiry date
    from datetime import timezone
    try:
        if isinstance(data['expiryDate'], str):
            # Parse the string to a datetime object with timezone info
            expiry_date = datetime.fromisoformat(data['expiryDate'].replace('Z', '+00:00'))
            # Ensure it has timezone info
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
        else:
            expiry_date = data['expiryDate']
            # Ensure it has timezone info
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
    except ValueError as e:
        print(f"Error parsing expiry date: {e}")
        return jsonify({"error": f"Invalid expiry date format: {str(e)}"}), 400
    
    # Get current time with timezone
    now_with_tz = datetime.now(timezone.utc)
    
    # Create the invitation document
    invitation_data = {
        'code': data['code'],
        'companyId': data['companyId'],
        'companyName': data['companyName'],
        'expiryDate': expiry_date,
        'createdAt': now_with_tz,
        'createdBy': user_info['uid'],
        'used': False
    }
    
    try:
        # Add the invitation to Firestore
        invitation_ref = db.collection('invitations').document(data['code'])
        invitation_ref.set(invitation_data)
        
        return jsonify({"success": True, "code": data['code']}), 201
    except Exception as e:
        print(f"Error creating invitation: {e}")
        print(traceback.format_exc())  # Print the full traceback for debugging
        return jsonify({"error": f"Failed to create invitation: {str(e)}"}), 500

# API endpoint to get an invitation by code
@api.route('/invitations/<code>', methods=['GET'])
def get_invitation(code):
    """Get an invitation by its code."""
    try:
        # Get the invitation from Firestore
        invitation_ref = db.collection('invitations').document(code)
        invitation = invitation_ref.get()
        
        if not invitation.exists:
            return jsonify({"error": "Invitation not found"}), 404
        
        invitation_data = invitation.to_dict()
        
        # Convert Firestore timestamp to ISO format for JSON serialization
        if 'expiryDate' in invitation_data:
            if hasattr(invitation_data['expiryDate'], 'isoformat'):
                # Ensure it has timezone info before converting to string
                from datetime import timezone
                expiry_date = invitation_data['expiryDate']
                if expiry_date.tzinfo is None:
                    expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                invitation_data['expiryDate'] = expiry_date.isoformat()
        
        if 'createdAt' in invitation_data:
            if hasattr(invitation_data['createdAt'], 'isoformat'):
                # Ensure it has timezone info before converting to string
                created_at = invitation_data['createdAt']
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                invitation_data['createdAt'] = created_at.isoformat()
        
        if 'usedAt' in invitation_data:
            if hasattr(invitation_data['usedAt'], 'isoformat'):
                # Ensure it has timezone info before converting to string
                used_at = invitation_data['usedAt']
                if used_at.tzinfo is None:
                    used_at = used_at.replace(tzinfo=timezone.utc)
                invitation_data['usedAt'] = used_at.isoformat()
        
        return jsonify(invitation_data), 200
    except Exception as e:
        print(f"Error getting invitation: {e}")
        print(traceback.format_exc())  # Print the full traceback for debugging
        return jsonify({"error": f"Failed to get invitation: {str(e)}"}), 500

# API endpoint to use an invitation
@api.route('/invitations/<code>/use', methods=['POST'])
def use_invitation(code):
    """Mark an invitation as used and add the user to the company."""
    # Get the authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"error": "Authorization header is required"}), 401
    
    # Verify the token and get user info
    user_info = get_user_from_token(auth_header)
    if not user_info:
        return jsonify({"error": "Invalid or expired token"}), 401
    
    # Get the request data
    data = request.json
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    # Validate required fields
    required_fields = ['userId', 'email']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    try:
        # Get the invitation from Firestore
        invitation_ref = db.collection('invitations').document(code)
        invitation = invitation_ref.get()
        
        if not invitation.exists:
            return jsonify({"error": "Invitation not found"}), 404
        
        invitation_data = invitation.to_dict()
        
        # Check if invitation is already used
        if invitation_data.get('used', False):
            return jsonify({"error": "This invitation has already been used"}), 400
        
        # Check if invitation is expired
        expiry_date = invitation_data.get('expiryDate')
        if expiry_date:
            # Convert to datetime if it's a string
            if isinstance(expiry_date, str):
                try:
                    expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                except ValueError:
                    print(f"Error parsing expiry date: {expiry_date}")
            
            # Make sure we're comparing timezone-aware datetimes
            from datetime import timezone
            now = datetime.now(timezone.utc)
            
            # If expiry_date is naive (no timezone info), make it timezone-aware
            if expiry_date.tzinfo is None:
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                
            # Now compare dates
            if expiry_date < now:
                return jsonify({"error": "This invitation has expired"}), 400
        
        # Get current time with timezone
        now_with_tz = datetime.now(timezone.utc)
        
        # Mark the invitation as used
        invitation_ref.update({
            'used': True,
            'usedBy': data['userId'],
            'usedAt': now_with_tz,
            'userEmail': data['email']
        })
        
        # Add the user to the company
        company_id = invitation_data.get('companyId')
        if company_id:
            # Check if the company exists
            company_ref = db.collection('companies').document(company_id)
            company = company_ref.get()
            
            if company.exists:
                # Add the user to the company's user list
                company_data = company.to_dict()
                user_ids = company_data.get('user_ids', [])
                if data['userId'] not in user_ids:
                    user_ids.append(data['userId'])
                    company_ref.update({'user_ids': user_ids})
                
                # Add the company to the user's company list
                user_ref = db.collection('users').document(data['userId'])
                user = user_ref.get()
                
                if user.exists:
                    user_data = user.to_dict()
                    company_ids = user_data.get('company_ids', [])
                    if company_id not in company_ids:
                        company_ids.append(company_id)
                        user_ref.update({'company_ids': company_ids})
                else:
                    # Create a new user document with empty profile fields
                    user_ref.set({
                        'uid': data['userId'],
                        'email': data['email'],
                        'display_name': data['email'].split('@')[0],
                        'role': 'user',
                        'company_ids': [company_id],
                        'created_at': now_with_tz,
                        **create_empty_profile()  # Add empty profile fields
                    })
        
        return jsonify({"success": True}), 200
    except Exception as e:
        print(f"Error using invitation: {e}")
        print(traceback.format_exc())  # Print the full traceback for debugging
        return jsonify({"error": f"Failed to use invitation: {str(e)}"}), 500

@api.route('/mandrill/templates', methods=['GET'])
def get_mandrill_templates():
    """Get all templates from Mandrill account."""
    try:
        # Get user from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization required'}), 401
        
        # Extract and verify token
        user_info = get_user_from_token(auth_header)
        if not user_info:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Only admins can get Mandrill templates
        if not is_admin(user_info):
            return jsonify({'error': 'Admin privileges required to access Mandrill templates'}), 403
        
        # Get templates from Mandrill
        templates = mandrill_service.get_templates()
        
        # Return only the name and slug for each template
        simplified_templates = [
            {'name': template['name'], 'slug': template['slug']}
            for template in templates
        ]
        
        return jsonify(simplified_templates), 200
        
    except Exception as e:
        print(f"Error getting Mandrill templates: {e}")
        return jsonify({'error': f'Error getting Mandrill templates: {str(e)}'}), 500

@api.route('/account/profile', methods=['GET'])
def get_profile():
    """Get user profile information."""
    auth_header = request.headers.get('Authorization')
    user_info = get_user_from_token(auth_header)
    
    if not user_info:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    try:
        print("Getting profile for user:", json.dumps(user_info, indent=2))
        
        # Get user data from Firestore
        user_ref = db.collection('users').document(user_info['uid'])
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            print(f"User document not found for uid: {user_info['uid']}")
            return jsonify({'error': 'User profile not found'}), 404
            
        user_data = user_doc.to_dict()
        print("Raw Firestore user data:", json.dumps(user_data, indent=2, default=str))
        
        # Return the profile data in the expected format
        profile_data = {
            "display_name": user_data.get('display_name'),
            "email": user_data.get('email'),
            "role": user_data.get('role'),
            "profile": user_data.get('profile', {})
        }
        
        print("Returning profile data:", json.dumps(profile_data, indent=2, default=str))
        return jsonify(profile_data), 200
        
    except Exception as e:
        print(f"Error fetching profile: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api.route('/account/profile', methods=['PATCH'])
def update_profile():
    """Update user profile information."""
    auth_header = request.headers.get('Authorization')
    user_info = get_user_from_token(auth_header)
    
    if not user_info:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    try:
        # Get the update data
        update_data = request.get_json()
        print("Update data received:", json.dumps(update_data, indent=2))
        
        # Get user reference
        user_ref = db.collection('users').document(user_info['uid'])
        
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
            "profile": updated_data.get('profile', {})
        }
        
        print("Updated profile:", json.dumps(formatted_data, indent=2, default=str))
        return jsonify(formatted_data), 200
        
    except Exception as e:
        print(f"Error updating profile: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api.route('/companies/<company_id>/billing', methods=['GET'])
def get_company_billing(company_id):
    """Get company billing information."""
    auth_header = request.headers.get('Authorization')
    user_info = get_user_from_token(auth_header)
    
    if not user_info:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    # Check if user has access to the company
    user_id = user_info.get('uid')
    if not is_admin(user_info) and not check_company_access(user_id, company_id):
        return jsonify({'error': 'Unauthorized access to this company'}), 403
    
    try:
        print(f"Getting billing info for company: {company_id}")
        
        # Get company data from Firestore
        company_ref = db.collection('companies').document(company_id)
        company_doc = company_ref.get()
        
        if not company_doc.exists:
            print(f"Company document not found for id: {company_id}")
            return jsonify({'error': 'Company not found'}), 404
            
        company_data = company_doc.to_dict()
        print("Raw Firestore company data:", json.dumps(company_data, indent=2, default=str))
        
        # Extract only billing-related data
        billing_data = company_data.get('billing', {
            'form_of_payment': 'credit',
            'payment_transferred': 0,
            'payment_due': 0,
            'payment_remaining': 0,
            'payment_history': []
        })
        
        print("Returning billing data:", json.dumps(billing_data, indent=2, default=str))
        return jsonify(billing_data), 200
        
    except Exception as e:
        print(f"Error in get_company_billing: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api.route('/companies/<company_id>/billing', methods=['PATCH'])
def update_company_billing(company_id):
    """Update company billing information."""
    auth_header = request.headers.get('Authorization')
    user_info = get_user_from_token(auth_header)
    
    if not user_info:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    # Only admins can update billing information
    if not is_admin(user_info):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    try:
        update_data = request.get_json()
        print("Update data received:", json.dumps(update_data, indent=2))
        
        # Validate form_of_payment if provided
        if 'form_of_payment' in update_data:
            valid_payment_forms = ['credit', 'check', 'wire_transfer']
            if update_data['form_of_payment'] not in valid_payment_forms:
                return jsonify({'error': 'Invalid form of payment'}), 400
        
        # Get company reference
        company_ref = db.collection('companies').document(company_id)
        company_doc = company_ref.get()
        
        if not company_doc.exists:
            return jsonify({'error': 'Company not found'}), 404
            
        current_data = company_doc.to_dict()
        current_billing = current_data.get('billing', {})
        
        # Update billing data
        billing_update = {
            'billing': {
                **current_billing,
                **update_data,
                'payment_remaining': (
                    current_billing.get('payment_due', 0) - 
                    current_billing.get('payment_transferred', 0)
                )
            }
        }
        
        # Update the billing info in Firestore
        company_ref.update(billing_update)
        
        # Get and return the updated billing data
        updated_doc = company_ref.get()
        updated_data = updated_doc.to_dict()
        billing_data = updated_data.get('billing', {})
        
        print("Updated billing info:", json.dumps(billing_data, indent=2, default=str))
        return jsonify(billing_data), 200
        
    except Exception as e:
        print(f"Error in update_company_billing: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api.route('/companies/<company_id>/billing/payment', methods=['POST'])
def add_company_payment(company_id):
    """Add a new payment to the company's payment history."""
    auth_header = request.headers.get('Authorization')
    user_info = get_user_from_token(auth_header)
    
    if not user_info:
        return jsonify({'error': 'Unauthorized access'}), 401
    
    # Only admins can add payments
    if not is_admin(user_info):
        return jsonify({'error': 'Admin privileges required'}), 403
    
    try:
        payment_data = request.get_json()
        print("Payment data received:", json.dumps(payment_data, indent=2))
        
        # Validate required fields
        if 'form_of_payment' not in payment_data or 'total' not in payment_data:
            return jsonify({'error': 'form_of_payment and total are required'}), 400
            
        # Validate form_of_payment
        valid_payment_forms = ['credit', 'check', 'wire_transfer']
        if payment_data['form_of_payment'] not in valid_payment_forms:
            return jsonify({'error': 'Invalid form of payment'}), 400
            
        # Validate total
        if not isinstance(payment_data['total'], (int, float)) or payment_data['total'] < 0:
            return jsonify({'error': 'Invalid payment total'}), 400
        
        # Get company reference
        company_ref = db.collection('companies').document(company_id)
        company_doc = company_ref.get()
        
        if not company_doc.exists:
            return jsonify({'error': 'Company not found'}), 404
            
        current_data = company_doc.to_dict()
        current_billing = current_data.get('billing', {})
        
        # Create new payment record with payment_id
        new_payment = {
            'payment_id': f"PAY-{uuid.uuid4().hex[:8].upper()}",  # Generate a random 8-character payment ID
            'form_of_payment': payment_data['form_of_payment'],
            'date_processed': datetime.now().isoformat(),
            'total': payment_data['total']
        }
        
        # Update payment history and totals
        payment_history = current_billing.get('payment_history', [])
        payment_history.append(new_payment)
        
        payment_transferred = current_billing.get('payment_transferred', 0) + payment_data['total']
        payment_due = current_billing.get('payment_due', 0)
        payment_remaining = payment_due - payment_transferred
        
        # Update billing data
        billing_update = {
            'billing': {
                **current_billing,
                'payment_transferred': payment_transferred,
                'payment_remaining': payment_remaining,
                'payment_history': payment_history
            }
        }
        
        # Update the billing info in Firestore
        company_ref.update(billing_update)
        
        # Get and return the updated billing data
        updated_doc = company_ref.get()
        updated_data = updated_doc.to_dict()
        billing_data = updated_data.get('billing', {})
        
        print("Updated billing info:", json.dumps(billing_data, indent=2, default=str))
        return jsonify(billing_data), 200
        
    except Exception as e:
        print(f"Error in add_company_payment: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api.route('/companies/<company_id>/billing/tiers', methods=['GET'])
def get_company_billing_tiers(company_id):
    """Get billing tiers for a company."""
    try:
        # Get user info from token
        user_info = get_user_from_token(request.headers.get('Authorization'))
        if not user_info:
            return jsonify({'error': 'Unauthorized'}), 401

        # Check if user has access to the company
        if not check_company_access(user_info['uid'], company_id):
            return jsonify({'error': 'Unauthorized access to company'}), 403

        # Get billing tiers from Firestore
        billing_tiers_ref = db.collection('companies').document(company_id).collection('billing').document('tiers')
        billing_tiers = billing_tiers_ref.get()

        if not billing_tiers.exists:
            # Return default tiers if not set
            default_tiers = {
                'current_tier': 'L01',
                'available_tiers': {
                    'L01': {
                        'name': 'L01 Standard',
                        'description': 'Standard tier with basic features',
                        'features': [
                            'Up to 5 AI agents',
                            'Basic analytics',
                            'Standard support',
                            'Core integrations'
                        ],
                        'limits': {
                            'ai_agents': 5,
                            'users': 10,
                            'storage': '10GB'
                        },
                        'price': 151600,
                        'active': True,
                        'isDefault': True
                    },
                    'L03_PRO': {
                        'name': 'L03 Pro',
                        'description': 'Advanced tier with unlimited capabilities',
                        'features': [
                            'Unlimited AI agents',
                            'Advanced analytics & reporting',
                            'Priority support',
                            'Custom integrations',
                            'Advanced security features'
                        ],
                        'limits': {
                            'ai_agents': -1,  # unlimited
                            'users': -1,  # unlimited
                            'storage': '100GB'
                        },
                        'price': 299900,
                        'active': False,
                        'isDefault': False,
                        'comingSoon': True
                    }
                },
                'last_updated': datetime.now().isoformat()
            }
            return jsonify(default_tiers)

        return jsonify(billing_tiers.to_dict())

    except Exception as e:
        print(f"Error getting billing tiers: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
