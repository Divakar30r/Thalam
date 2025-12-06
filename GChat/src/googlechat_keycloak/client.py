"""
Google Chat API Client
Provides methods to interact with Google Chat API using Keycloak WIF authentication
"""

import requests
import json
from datetime import datetime
from typing import List, Dict, Optional
from .auth import KeycloakWIFAuth
from .config import GOOGLE_CHAT_CONFIG


class GoogleChatClient:
    """
    Google Chat API client with Keycloak Workload Identity Federation authentication
    """
    
    def __init__(self):
        self.auth = KeycloakWIFAuth()
        self.base_url = GOOGLE_CHAT_CONFIG['api_endpoint']
        self.user_email = GOOGLE_CHAT_CONFIG['user_email']
        self._headers = None

    def _normalize_space(self, space_name: str) -> Optional[str]:
        """
        Normalize space identifier to the short id (strip leading 'spaces/' if present)
        """
        if not space_name:
            return None
        return space_name.split('/')[-1]
    
    def _get_headers(self):
        """
        Get authenticated headers for API requests
        """
        if not self._headers:
            access_token = self.auth.authenticate()
            self._headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
        return self._headers
    
    def _refresh_headers(self):
        """
        Refresh authentication headers
        """
        self._headers = None
        return self._get_headers()
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, params: Dict = None):
        """
        Make authenticated API request
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, params=params)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, params=params)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle authentication errors by refreshing token
            if response.status_code == 401:
                print("Authentication token expired, refreshing...")
                headers = self._refresh_headers()
                
                # Retry the request with new token
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, params=params)
                elif method.upper() == 'POST':
                    response = requests.post(url, headers=headers, json=data, params=params)
                elif method.upper() == 'PUT':
                    response = requests.put(url, headers=headers, json=data, params=params)
                elif method.upper() == 'DELETE':
                    response = requests.delete(url, headers=headers, params=params)
            
            response.raise_for_status()
            
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text}")
            raise
    
    def list_spaces(self, page_size: int = 100) -> Dict:
        """
        List all spaces the bot has access to
        """
        params = {
            'pageSize': page_size
        }
        return self._make_request('GET', 'spaces', params=params)
    
    def get_space(self, space_name: str) -> Dict:
        """
        Get details of a specific space
        """
        space_name = self._normalize_space(space_name)
        return self._make_request('GET', f'spaces/{space_name}')
    
    def create_message(self, space_name: str, text: str, thread_key: str = None) -> Dict:
        """
        Create a message in a space
        """
        message_data = {
            'text': text
        }
        
        params = {}
        if thread_key:
            params['threadKey'] = thread_key
        space_name = self._normalize_space(space_name)
        return self._make_request('POST', f'spaces/{space_name}/messages', data=message_data, params=params)
    
    def create_card_message(self, space_name: str, card_data: Dict, thread_key: str = None) -> Dict:
        """
        Create a card message in a space
        """
        message_data = {
            'cardsV2': [card_data]
        }
        
        params = {}
        if thread_key:
            params['threadKey'] = thread_key
        space_name = self._normalize_space(space_name)
        return self._make_request('POST', f'spaces/{space_name}/messages', data=message_data, params=params)
    
    def list_messages(self, space_name: str, page_size: int = 25) -> Dict:
        """
        List messages in a space
        """
        params = {
            'pageSize': page_size
        }
        space_name = self._normalize_space(space_name)
        return self._make_request('GET', f'spaces/{space_name}/messages', params=params)
    
    def get_message(self, message_name: str) -> Dict:
        """
        Get a specific message
        """
        return self._make_request('GET', f'messages/{message_name}')
    
    def update_message(self, message_name: str, text: str) -> Dict:
        """
        Update a message
        """
        message_data = {
            'text': text
        }
        
        params = {
            'updateMask': 'text'
        }
        
        return self._make_request('PUT', f'messages/{message_name}', data=message_data, params=params)
    
    def delete_message(self, message_name: str) -> Dict:
        """
        Delete a message
        """
        return self._make_request('DELETE', f'messages/{message_name}')
    
    def list_members(self, space_name: str) -> Dict:
        """
        List members of a space
        """
        space_name = self._normalize_space(space_name)
        return self._make_request('GET', f'spaces/{space_name}/members')
    
    def get_member(self, member_name: str) -> Dict:
        """
        Get details of a specific member
        """
        return self._make_request('GET', f'members/{member_name}')
    
    def create_reaction(self, message_name: str, emoji: str) -> Dict:
        """
        Add a reaction to a message
        """
        reaction_data = {
            'emoji': {
                'unicode': emoji
            }
        }
        return self._make_request('POST', f'messages/{message_name}/reactions', data=reaction_data)
    
    def delete_reaction(self, reaction_name: str) -> Dict:
        """
        Delete a reaction
        """
        return self._make_request('DELETE', f'reactions/{reaction_name}')
    
    def upload_attachment(self, space_name: str, file_path: str) -> Dict:
        """
        Upload an attachment to a space
        Note: This is a simplified version. Full implementation would require multipart upload
        """
        # This would require implementing multipart/form-data upload
        # For now, this is a placeholder
        raise NotImplementedError("File upload functionality needs to be implemented with multipart upload")
    
    def create_webhook(self, space_name: str, webhook_url: str) -> Dict:
        """
        Create a webhook for a space (if supported)
        Note: This might require additional setup and permissions
        """
        webhook_data = {
            'targetUrl': webhook_url
        }
        space_name = self._normalize_space(space_name)
        return self._make_request('POST', f'spaces/{space_name}/webhooks', data=webhook_data)


class GoogleChatBot:
    """
    Higher-level bot interface for Google Chat
    """
    
    def __init__(self, bot_name: str = "Keycloak Chat Bot"):
        self.client = GoogleChatClient()
        self.bot_name = bot_name
    
    def send_simple_message(self, space_name: str, message: str) -> Dict:
        """
        Send a simple text message
        """
        return self.client.create_message(space_name, message)
    
    def send_notification_card(self, space_name: str, title: str, subtitle: str, message: str) -> Dict:
        """
        Send a notification card
        """
        card_data = {
            'card': {
                'header': {
                    'title': title,
                    'subtitle': subtitle
                },
                'sections': [
                    {
                        'widgets': [
                            {
                                'textParagraph': {
                                    'text': message
                                }
                            }
                        ]
                    }
                ]
            }
        }
        return self.client.create_card_message(space_name, card_data)
    
    def send_interactive_card(self, space_name: str, title: str, buttons: List[Dict]) -> Dict:
        """
        Send an interactive card with buttons
        """
        widgets = [
            {
                'textParagraph': {
                    'text': title
                }
            }
        ]
        
        for button in buttons:
            widgets.append({
                'buttonList': {
                    'buttons': [
                        {
                            'text': button.get('text', 'Button'),
                            'onClick': {
                                'action': {
                                    'actionMethodName': button.get('action', 'default_action'),
                                    'parameters': button.get('parameters', [])
                                }
                            }
                        }
                    ]
                }
            })
        
        card_data = {
            'card': {
                'sections': [
                    {
                        'widgets': widgets
                    }
                ]
            }
        }
        
        return self.client.create_card_message(space_name, card_data)
    
    def monitor_space(self, space_name: str, callback_function):
        """
        Monitor a space for new messages (basic polling implementation)
        For production, consider using webhooks instead
        """
        import time
        
        last_messages = set()
        
        while True:
            try:
                messages = self.client.list_messages(space_name)
                current_messages = set()
                
                if 'messages' in messages:
                    for message in messages['messages']:
                        message_id = message.get('name', '')
                        current_messages.add(message_id)
                        
                        if message_id not in last_messages:
                            # New message found
                            callback_function(message)
                
                last_messages = current_messages
                time.sleep(5)  # Poll every 5 seconds
                
            except KeyboardInterrupt:
                print("Monitoring stopped by user")
                break
            except Exception as e:
                print(f"Error monitoring space: {e}")
                time.sleep(10)  # Wait longer on error