import os
import requests
import json
from typing import List, Dict, Any, Optional

class MandrillEmailService:
    """Service for sending emails using Mandrill API."""
    
    def __init__(self, api_key: str = None):
        """Initialize the Mandrill email service with the API key."""
        print("\n=== MANDRILL SERVICE INITIALIZATION ===")
        print(f"API Key provided directly: {bool(api_key)}")
        print(f"API Key in environment: {bool(os.environ.get('MANDRILL_API_KEY'))}")
        
        self.enabled = False
        
        # Try to get API key
        self.api_key = api_key or os.environ.get('MANDRILL_API_KEY')
        if not self.api_key:
            print("WARNING: Mandrill API key not found. Email functionality will be disabled.")
            print("=====================================\n")
            return
            
        # If we have an API key, proceed with initialization
        if os.environ.get('MANDRILL_API_KEY'):
            print(f"Environment API key length: {len(os.environ.get('MANDRILL_API_KEY'))}")
            print(f"Environment API key format: {repr(os.environ.get('MANDRILL_API_KEY'))}")
            
        # Clean the API key
        self.api_key = self.api_key.strip()
        print(f"Final API key length: {len(self.api_key)}")
        print(f"Final API key format: {repr(self.api_key)}")
        
        self.base_url = "https://mandrillapp.com/api/1.0"
        print(f"MandrillEmailService initialized with API key: {self.api_key[:4]}...{self.api_key[-4:]}")
        self.enabled = True
        print("=====================================\n")
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """Get all templates from Mandrill account."""
        if not self.enabled:
            print("WARNING: Mandrill service not enabled. Cannot get templates.")
            return []
            
        endpoint = f"{self.base_url}/templates/list.json"
        payload = {"key": self.api_key}
        
        try:
            print(f"Sending request to Mandrill API: {endpoint}")
            response = requests.post(endpoint, json=payload, timeout=10)
            
            # Try to parse the response as JSON
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                print(f"Failed to parse Mandrill API response as JSON: {response.text}")
                raise ValueError(f"Invalid response from Mandrill API: {response.text[:100]}")
            
            # Check for Mandrill API errors
            if not response.ok:
                error_message = response_data.get('message', 'Unknown Mandrill API error')
                print(f"Mandrill API error: {error_message}")
                raise ValueError(f"Mandrill API error: {error_message}")
            
            print(f"Successfully retrieved {len(response_data)} templates from Mandrill")
            return response_data
            
        except requests.exceptions.Timeout:
            print("Timeout connecting to Mandrill API")
            raise ValueError("Connection to Mandrill API timed out")
        except requests.exceptions.ConnectionError:
            print("Connection error to Mandrill API")
            raise ValueError("Failed to connect to Mandrill API")
        except Exception as e:
            print(f"Unexpected error getting Mandrill templates: {str(e)}")
            raise ValueError(f"Error getting Mandrill templates: {str(e)}")
    
    def send_template_email(
        self,
        template_name: str,
        subject: str,
        from_email: str,
        from_name: str,
        to_emails: List[Dict[str, str]],
        merge_vars: Optional[List[Dict[str, Any]]] = None,
        global_merge_vars: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Send an email using a Mandrill template.
        
        Args:
            template_name: The name of the template in Mandrill
            subject: Email subject
            from_email: Sender email address
            from_name: Sender name
            to_emails: List of recipient dictionaries with 'email' and 'name' keys
            merge_vars: List of dictionaries with recipient-specific merge variables
            global_merge_vars: List of dictionaries with global merge variables
            
        Returns:
            List of response dictionaries from Mandrill API
        """
        if not self.enabled:
            print("WARNING: Mandrill service not enabled. Cannot send email.")
            return []
            
        endpoint = f"{self.base_url}/messages/send-template.json"
        
        # Prepare the payload
        payload = {
            "key": self.api_key,
            "template_name": template_name,
            "template_content": [],  # Required by API but not used
            "message": {
                "subject": subject,
                "from_email": from_email,
                "from_name": from_name,
                "to": to_emails,
                "important": False,
                "track_opens": True,
                "track_clicks": True,
                "auto_text": True,
                "auto_html": True,
                "inline_css": True,
            }
        }
        
        # Add merge variables if provided
        if global_merge_vars:
            payload["message"]["global_merge_vars"] = global_merge_vars
            
        if merge_vars:
            payload["message"]["merge_vars"] = merge_vars
        
        try:
            print(f"Sending email with template '{template_name}' to {len(to_emails)} recipients")
            print(f"From: {from_name} <{from_email}>")
            print(f"Request payload: {json.dumps(payload, default=str)[:500]}...")
            
            # Send the request
            response = requests.post(endpoint, json=payload, timeout=15)
            
            # Try to parse the response as JSON
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                print(f"Failed to parse Mandrill API response as JSON: {response.text}")
                raise ValueError(f"Invalid response from Mandrill API: {response.text[:100]}")
            
            # Check for Mandrill API errors
            if not response.ok:
                error_message = response_data.get('message', 'Unknown Mandrill API error')
                print(f"Mandrill API error: {error_message}")
                
                # Check for common errors
                if 'Invalid template' in error_message:
                    raise ValueError(f"Invalid template name: {template_name}. Please check that this template exists in your Mandrill account.")
                elif 'Invalid key' in error_message:
                    raise ValueError("Invalid Mandrill API key. Please check your API key configuration.")
                else:
                    raise ValueError(f"Mandrill API error: {error_message}")
            
            # Check for rejected emails
            rejected_emails = [result for result in response_data if result.get('status') == 'rejected']
            if rejected_emails:
                rejected_addresses = [result.get('email') for result in rejected_emails]
                reject_reasons = [result.get('reject_reason') for result in rejected_emails]
                
                print(f"Some emails were rejected: {rejected_addresses}")
                print(f"Rejection reasons: {reject_reasons}")
                
                # Check for domain mismatch errors
                domain_mismatch = [result for result in rejected_emails if result.get('reject_reason') == 'recipient-domain-mismatch']
                if domain_mismatch:
                    domain_mismatch_addresses = [result.get('email') for result in domain_mismatch]
                    domains = list(set([email.split('@')[1] for email in domain_mismatch_addresses if '@' in email]))
                    
                    error_message = (
                        f"Email sending failed due to unverified recipient domains: {', '.join(domains)}. "
                        f"These domains need to be verified in your Mandrill account before sending emails to them."
                    )
                    print(error_message)
                    
                    # Return the full response data so the caller can handle it
                    return response_data
            
            print(f"Email sent successfully. Response: {json.dumps(response_data)[:500]}...")
            return response_data
            
        except requests.exceptions.Timeout:
            print("Timeout connecting to Mandrill API")
            raise ValueError("Connection to Mandrill API timed out")
        except requests.exceptions.ConnectionError:
            print("Connection error to Mandrill API")
            raise ValueError("Failed to connect to Mandrill API")
        except Exception as e:
            print(f"Unexpected error sending email: {str(e)}")
            raise ValueError(f"Error sending email: {str(e)}") 