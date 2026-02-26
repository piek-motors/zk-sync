import json
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any

import requests


class ERPUploader:
    """Upload attendance events to ERP system."""
    
    def __init__(self, base_url: str, email: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.email = email
        self.password = password
        self.access_token: str | None = None
        self.session = requests.Session()
        self.session.timeout = 30
    
    def login(self) -> None:
        """Authenticate and get access token."""
        auth_data = {
            'email': self.email,
            'password': self.password,
        }
        
        response = self.session.post(
            f'{self.base_url}/api/login',
            json=auth_data,
            headers={'Content-Type': 'application/json'},
        )
        response.raise_for_status()
        
        auth_response = response.json()
        self.access_token = auth_response['accessToken']
        self.session.headers['Authorization'] = f'Bearer {self.access_token}'
    
    def upload_events(
        self,
        employees: List[Dict[str, str]],
        events: List[Tuple[str, int]],
    ) -> None:
        """Upload employees and events to ERP.
        
        Args:
            employees: List of dicts with keys: first_name, last_name, card
            events: List of tuples (card, unix_timestamp)
        """
        # Convert employees to DTO format: [firstname, lastname, card]
        employee_dtos = [
            [e['first_name'], e['last_name'], e['card']]
            for e in employees
        ]
        
        # Convert events to DTO format: [card, timestamp] (no id)
        event_dtos = [
            [card, ts]
            for card, ts in events
        ]
        
        upload_data = {
            'employees': employee_dtos,
            'events': event_dtos,
        }
        
        response = self.session.post(
            f'{self.base_url}/trpc/hr.attendance_upload_data',
            json=upload_data,
            headers={'Content-Type': 'application/json'},
        )
        response.raise_for_status()
        
        print(f"Upload response:\n{json.dumps(response.json(), indent=2)}")


def filter_events_by_days(
    events: List[Tuple[str, int]],
    days: int = 5,
) -> List[Tuple[str, int]]:
    """Filter events to include only those from the last N days.
    
    Args:
        events: List of tuples (card, unix_timestamp)
        days: Number of days to look back
    
    Returns:
        Filtered list of events
    """
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp())
    return [(card, ts) for card, ts in events if ts >= cutoff]
