#!/usr/bin/env python3
import os
import sys
import uuid
import click
from datetime import datetime, timezone
from typing import Optional

# Add the parent directory to sys.path to fix imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.models import OnboardingStep, OnboardingStatus
from config.firebase_config import db
from firebase_admin import firestore

def get_maven_company():
    """Get Maven company document if it exists"""
    companies = db.collection('companies').where('name', '==', 'Maven').limit(1).stream()
    return next(companies, None)

def create_maven_steps():
    """Create default Maven onboarding steps"""
    return [
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Account setup",
            description="Initial account setup and configuration",
            status=OnboardingStatus.TODO,
            buttonText="Go to Account Setup",
            todoLink="/account/setup"
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Payment Processed",
            description="Confirm payment has been processed successfully",
            status=OnboardingStatus.TODO,
            buttonText="Go to Billing",
            todoLink="/billing"
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Data integration",
            description="Connect and integrate your data sources",
            status=OnboardingStatus.TODO,
            buttonText="Go to Data Integration",
            todoLink="/data/integration"
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Build your AI team",
            description="Initial meeting to discuss AI team composition",
            status=OnboardingStatus.TODO,
            buttonText="Schedule Meeting",
            todoLink="/ai/team"
        ),
        OnboardingStep(
            id=str(uuid.uuid4()),
            name="Training the AI",
            description="Initial AI training with your data",
            status=OnboardingStatus.TODO,
            buttonText="Start Training",
            todoLink="/ai/training"
        )
    ]

@click.group()
def cli():
    """Maven Company Management CLI"""
    pass

@cli.command()
@click.option('--user-email', prompt='Enter user email to assign', help='Email of the user to assign to Maven')
def create(user_email: str):
    """Create a new Maven company with default structure"""
    try:
        # Check if Maven company already exists
        existing_company = get_maven_company()
        if existing_company:
            click.echo(click.style('❌ Maven company already exists!', fg='red'))
            return
        
        # Create company data
        company_data = {
            'name': 'Maven',
            'onboarding_steps': [step.to_dict() for step in create_maven_steps()],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'user_ids': [],
            'team_members': [],
            'data_sharing': {
                'is_connected': False,
                'connection_type': None,
                'connected_at': None,
                'connection_details': {}
            },
            'output_library': {
                'files': [],
                'total_files': 0,
                'total_size_bytes': 0
            },
            'billing': {
                'form_of_payment': 'credit',
                'payment_transferred': 0,
                'payment_due': 0,
                'payment_remaining': 0,
                'payment_history': [],
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
                            'ai_agents': -1,
                            'users': -1,
                            'storage': '100GB'
                        },
                        'price': 299900,
                        'active': False,
                        'isDefault': False,
                        'comingSoon': True
                    }
                }
            }
        }
        
        # Add to Firestore
        company_ref = db.collection('companies').document()
        company_ref.set(company_data)
        company_id = company_ref.id
        
        click.echo(click.style(f'✅ Successfully created Maven company with ID: {company_id}', fg='green'))
        
        # Assign user if email provided
        if user_email:
            assign_user(company_id, user_email)
            
    except Exception as e:
        click.echo(click.style(f'❌ Error creating Maven company: {str(e)}', fg='red'))

@cli.command()
@click.option('--user-email', prompt='Enter user email to assign', help='Email of the user to assign to Maven')
def assign(user_email: str):
    """Assign a user to the Maven company"""
    maven_doc = get_maven_company()
    if not maven_doc:
        click.echo(click.style('❌ Maven company not found', fg='red'))
        return
    
    assign_user(maven_doc.id, user_email)

def assign_user(company_id: str, user_email: str):
    """Helper function to assign a user to a company"""
    try:
        # Find user by email
        users_ref = db.collection('users')
        query = users_ref.where('email', '==', user_email).limit(1)
        user_docs = list(query.stream())
        
        if not user_docs:
            click.echo(click.style(f'❌ User with email {user_email} not found', fg='red'))
            return
            
        user_id = user_docs[0].id
        user_data = user_docs[0].to_dict()
        
        # Update user's company_ids
        company_ids = user_data.get('company_ids', [])
        if company_id not in company_ids:
            company_ids.append(company_id)
            users_ref.document(user_id).update({'company_ids': company_ids})
        
        # Update company's user_ids
        company_ref = db.collection('companies').document(company_id)
        company_data = company_ref.get().to_dict()
        user_ids = company_data.get('user_ids', [])
        if user_id not in user_ids:
            user_ids.append(user_id)
            company_ref.update({'user_ids': user_ids})
        
        click.echo(click.style(f'✅ Successfully assigned user {user_email} to Maven company', fg='green'))
        
    except Exception as e:
        click.echo(click.style(f'❌ Error assigning user: {str(e)}', fg='red'))

@cli.command()
def migrate_billing():
    """Migrate billing data from user to company"""
    try:
        # Get Maven company
        maven_doc = get_maven_company()
        if not maven_doc:
            click.echo(click.style('❌ Maven company not found', fg='red'))
            return
        
        # Get user billing data
        user_ref = db.collection('users').document('D6aEKB8QZ7dhrWaMV9ManiYUt6m1')
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            click.echo(click.style('❌ User not found', fg='red'))
            return
        
        user_data = user_doc.to_dict()
        billing_data = user_data.get('billing', {})
        
        if not billing_data:
            click.echo(click.style('❌ No billing data found', fg='red'))
            return
        
        # Update company billing
        company_ref = db.collection('companies').document(maven_doc.id)
        company_ref.update({'billing': billing_data})
        
        # Remove billing from user
        user_ref.update({'billing': firestore.DELETE_FIELD})
        
        click.echo(click.style(f'✅ Successfully migrated billing data to company {maven_doc.id}', fg='green'))
        
    except Exception as e:
        click.echo(click.style(f'❌ Error migrating billing data: {str(e)}', fg='red'))

@cli.command()
def update():
    """Update Maven company structure"""
    try:
        maven_doc = get_maven_company()
        if not maven_doc:
            click.echo(click.style('❌ Maven company not found', fg='red'))
            return
        
        company_ref = db.collection('companies').document(maven_doc.id)
        current_data = maven_doc.to_dict()
        
        # Update with expanded structure
        expanded_data = {
            'team_members': current_data.get('team_members', []),
            'data_sharing': current_data.get('data_sharing', {
                'is_connected': False,
                'connection_type': None,
                'connected_at': None,
                'connection_details': {}
            }),
            'output_library': current_data.get('output_library', {
                'files': [],
                'total_files': 0,
                'total_size_bytes': 0
            })
        }
        
        company_ref.update(expanded_data)
        click.echo(click.style('✅ Successfully updated Maven company structure', fg='green'))
        
    except Exception as e:
        click.echo(click.style(f'❌ Error updating Maven company: {str(e)}', fg='red'))

if __name__ == '__main__':
    cli() 