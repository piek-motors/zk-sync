import json
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any

import requests

from models import Event


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
        
        try:
            response.raise_for_status()
        except requests.HTTPError:
            try:
                error_data = response.json()
                error_msg = error_data.get('message', str(error_data))
            except (json.JSONDecodeError, ValueError):
                error_msg = response.text or response.reason
            raise RuntimeError(f"Login failed: {error_msg}")
        
        auth_response = response.json()
        self.access_token = auth_response['accessToken']
        self.session.headers['Authorization'] = f'Bearer {self.access_token}'
    
    def upload_events(
        self,
        employees: List[Dict[str, str]],
        events: List[Event],
    ) -> dict:
        """Upload employees and events to ERP.

        Args:
            employees: List of dicts with keys: first_name, last_name, card
            events: List of Event objects

        Returns:
            Server response as dict
        """
        # Convert employees to DTO format: [firstname, lastname, card]
        employee_dtos = [
            [e['first_name'], e['last_name'], e['card']]
            for e in employees
        ]

        # Convert events to DTO format using to_dto() method
        event_dtos = [event.to_dto() for event in events]

        upload_data = {
            'employees': employee_dtos,
            'events': event_dtos,
        }

        print(f"Uploading {len(employee_dtos)} employees and {len(event_dtos)} events...")
        if len(employee_dtos) == 0:
            print("WARNING: No employees provided - server may reject empty employees array")

        response = self.session.post(
            f'{self.base_url}/trpc/hr.attendance.upload_data',
            json=upload_data,
            headers={'Content-Type': 'application/json'},
        )

        try:
            response.raise_for_status()
        except requests.HTTPError:
            try:
                error_data = response.json()
                error_msg = error_data.get('message', str(error_data))
            except (json.JSONDecodeError, ValueError):
                error_msg = response.text or response.reason
            raise RuntimeError(f"Upload failed: {error_msg}")

        result = response.json()
        print(f"Upload response:\n{json.dumps(result, indent=2)}")
        return result


def filter_events_by_days(
    events: List[Event],
    days: int = 5,
) -> List[Event]:
    """Filter events to include only those from the last N days.

    Args:
        events: List of Event objects
        days: Number of days to look back

    Returns:
        Filtered list of events
    """
    cutoff = int((datetime.now() - timedelta(days=days)).timestamp())
    return [event for event in events if event.timestamp >= cutoff]
