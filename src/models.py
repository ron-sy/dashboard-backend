from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime

class OnboardingStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress" 
    DONE = "done"

class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"

class OnboardingStep:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        status: OnboardingStatus = OnboardingStatus.TODO,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.status = status
        self.updated_at = updated_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OnboardingStep':
        """Create OnboardingStep from Firestore document data"""
        status = OnboardingStatus(data.get('status', OnboardingStatus.TODO))
        updated_at = data.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            description=data.get('description', ''),
            status=status,
            updated_at=updated_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert OnboardingStep to dictionary for Firestore"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class User:
    def __init__(
        self,
        id: str,
        email: str,
        display_name: str = "",
        role: UserRole = UserRole.USER,
        company_ids: List[str] = None,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.email = email
        self.display_name = display_name
        self.role = role
        self.company_ids = company_ids or []
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], user_id: str) -> 'User':
        """Create User from Firestore document data"""
        role = UserRole(data.get('role', UserRole.USER))
        
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return cls(
            id=user_id,
            email=data.get('email', ''),
            display_name=data.get('display_name', ''),
            role=role,
            company_ids=data.get('company_ids', []),
            created_at=created_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert User to dictionary for Firestore"""
        return {
            'email': self.email,
            'display_name': self.display_name,
            'role': self.role,
            'company_ids': self.company_ids,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @property
    def is_admin(self) -> bool:
        """Check if the user has admin role"""
        return self.role == UserRole.ADMIN

class Company:
    def __init__(
        self,
        id: str,
        name: str,
        onboarding_steps: List[OnboardingStep] = None,
        created_at: Optional[datetime] = None,
        user_ids: List[str] = None
    ):
        self.id = id
        self.name = name
        self.onboarding_steps = onboarding_steps or []
        self.created_at = created_at or datetime.now()
        self.user_ids = user_ids or []
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], company_id: str) -> 'Company':
        """Create Company from Firestore document data"""
        steps = []
        steps_data = data.get('onboarding_steps', [])
        
        if isinstance(steps_data, list):
            for step_data in steps_data:
                steps.append(OnboardingStep.from_dict(step_data))
        
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return cls(
            id=company_id,
            name=data.get('name', ''),
            onboarding_steps=steps,
            created_at=created_at,
            user_ids=data.get('user_ids', [])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Company to dictionary for Firestore"""
        return {
            'name': self.name,
            'onboarding_steps': [step.to_dict() for step in self.onboarding_steps],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_ids': self.user_ids
        }

# Default onboarding steps template
DEFAULT_ONBOARDING_STEPS = [
    OnboardingStep(
        id="payment",
        name="First Payment",
        description="Complete the initial payment for onboarding",
        status=OnboardingStatus.TODO
    ),
    OnboardingStep(
        id="data_sharing",
        name="Share Company Data",
        description="Upload and share necessary company data",
        status=OnboardingStatus.TODO
    ),
    OnboardingStep(
        id="model_finetuning",
        name="Finetune Models",
        description="Customize and finetune models for your specific needs",
        status=OnboardingStatus.TODO
    ),
    OnboardingStep(
        id="physical_meeting",
        name="Physical Meeting",
        description="Schedule and complete the initial in-person meeting",
        status=OnboardingStatus.TODO
    )
]
