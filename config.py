import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()


def _parse_ip_codes(ip_codes_str: str | None) -> List[Dict[str, int | str]]:
    """Parse comma-separated IP:origin_id pairs into a list of dicts.

    Format: "192.168.1.1:001,192.168.1.2:002"
    Returns: [{"ip": "192.168.1.1", "origin_id": 1}, ...]
    """
    if not ip_codes_str:
        return []

    result = []
    for pair in ip_codes_str.split(','):
        pair = pair.strip()
        if ':' in pair:
            ip, origin_id = pair.split(':', 1)
            try:
                result.append({'ip': ip.strip(), 'origin_id': int(origin_id.strip())})
            except ValueError:
                pass  # Skip invalid origin_id values
    return result


config: dict = {
    'ip_codes': _parse_ip_codes(os.getenv('IP_CODES')),
    'password': os.getenv('PASSWORD', ''),
    'erp_login': os.getenv('ERP_LOGIN', ''),
    'erp_password': os.getenv('ERP_PASSWORD', ''),
    'erp_base_url': os.getenv('ERP_BASE_URL', ''),
}
