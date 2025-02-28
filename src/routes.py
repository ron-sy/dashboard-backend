import sys
import os
from flask import Blueprint, request, jsonify
from firebase_admin import auth
import json

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.firebase_config import db
from models import Company, OnboardingStep, OnboardingStatus, DEFAULT_ONBOARDING_STEPS
from models import User, UserRole
from typing import Dict, List, Any, Optional
from datetime import datetime

# Create a Blueprint for API routes
api = Blueprint('api', __name__)

# Always use production Firebase, never use development mode
DEV_MODE = False

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

def verify_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Verify Firebase ID token and return user info."""
    # In development mode, skip auth
    if DEV_MODE:
        print("DEV MODE: Skipping token verification")
        return {"uid": "dev-user-123", "email": "dev@example.com"}
    
    try:
        # First try to verify with Firebase Auth
        decoded_token = auth.verify_id_token(id_token)
        print(f"Token verified for user: {decoded_token.get('email', 'unknown')}")
        
        # Check if user exists in Firestore, if not create them
        user_id = decoded_token.get('uid')
        user_email = decoded_token.get('email')
        if user_id and user_email:
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                print(f"Creating new user record in Firestore for: {user_email}")
                # Create a minimal user record
                user_data = {
                    'email': user_email,
                    'display_name': decoded_token.get('name', user_email.split('@')[0]),
                    'role': UserRole.USER,  # Default role
                    'company_ids': [],
                    'created_at': datetime.now().isoformat()
                }
                user_ref.set(user_data)
        
        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {e}")
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
            
        # Create the user in Firestore
        user_ref = db.collection('users').document(uid)
        user_data = {
            'email': email,
            'display_name': display_name,
            'role': role,
            'company_ids': company_ids,
            'created_at': datetime.now().isoformat()
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
            'created_at': datetime.now().isoformat()
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
        
        # Prepare response object
        response = {
            'id': company.id,
            'name': company.name,
            'onboarding_steps': [step.to_dict() for step in company.onboarding_steps],
            'created_at': company.created_at.isoformat() if company.created_at else None,
            'user_ids': company.user_ids,
            'user_is_admin': is_user_admin  # Include this flag for frontend to determine edit permissions
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
        
        # Get company details
        company_ref = db.collection('companies').document(company_id)
        company_doc = company_ref.get()
        
        if not company_doc.exists:
            return jsonify({'error': 'Company not found'}), 404
        
        company_data = company_doc.to_dict()
        company = Company.from_dict(company_data, company_id)
        
        return jsonify([step.to_dict() for step in company.onboarding_steps]), 200
        
    except Exception as e:
        print(f"Error fetching onboarding steps: {e}")
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
        
        # Validate status
        try:
            new_status = OnboardingStatus(data['status'])
        except ValueError:
            return jsonify({'error': 'Invalid status value'}), 400
        
        # Get company details
        company_ref = db.collection('companies').document(company_id)
        company_doc = company_ref.get()
        
        if not company_doc.exists:
            return jsonify({'error': 'Company not found'}), 404
        
        company_data = company_doc.to_dict()
        company = Company.from_dict(company_data, company_id)
        
        # Find and update the step
        step_found = False
        for step in company.onboarding_steps:
            if step.id == step_id:
                step_found = True
                step.status = new_status
                step.updated_at = datetime.now()
                
                # Update in Firestore
                company_ref.update({
                    'onboarding_steps': [s.to_dict() for s in company.onboarding_steps]
                })
                
                print(f"Admin {user_info.get('uid')} updated step {step_id} status to {new_status}")
                
                return jsonify(step.to_dict()), 200
        
        if not step_found:
            return jsonify({'error': 'Onboarding step not found'}), 404
            
    except Exception as e:
        print(f"Error updating onboarding step: {e}")
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
