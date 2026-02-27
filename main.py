import argparse
from datetime import timedelta, timezone

from pyzkaccess import ZKAccess

import config
from erp_uploader import ERPUploader, filter_events_by_days
from models import Event


def fetch_all_transactions(unread_only: bool = False):
    """Fetch all transactions from all configured devices.

    Args:
        unread_only: If True, fetch only unread transactions.
    """
    all_transactions = []

    for ip_config in config.config['ip_codes']:
        ip = ip_config['ip']
        origin_id = ip_config['origin_id']

        connstr = f'protocol=TCP,ipaddress={ip},port=4370,timeout=4000,passwd={config.config["password"]}'

        with ZKAccess(connstr=connstr) as zk:
            query = zk.table('Transaction')
            if unread_only:
                query = query.unread()
            for txn in query:
                txn_dict = txn.dict
                txn_dict['device_ip'] = ip
                txn_dict['origin_id'] = origin_id
                all_transactions.append(txn_dict)

    return all_transactions


def upload_to_erp(unread_only: bool = False):
    """Fetch events from devices and upload to ERP.
    
    Args:
        unread_only: If True, fetch only unread transactions.
    """
    # Fetch all transactions
    transactions = fetch_all_transactions(unread_only=unread_only)

    # Convert to Event objects
    events = [
        Event(
            card=txn['card'],
            timestamp=int(txn['time'].timestamp()),
            origin_id=txn['origin_id'],
        )
        for txn in transactions
        if txn.get('card')
    ]

    # Sort by timestamp
    events.sort(key=lambda e: e.timestamp)

    # Filter to last 5 days
    events = filter_events_by_days(events, days=30)

    print(f"Total events (last 5 days): {len(events)}")

    # Upload to ERP
    uploader = ERPUploader(
        base_url=config.config['erp_base_url'],
        email=config.config['erp_login'],
        password=config.config['erp_password'],
    )
    uploader.login()

    # For now, upload events without employees
    # You'll need to provide employees list separately
    uploader.upload_events(employees=[], events=events)

    print(f"Uploaded {len(events)} events")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync attendance data to ERP')
    parser.add_argument('--unread', action='store_true', help='Fetch only unread transactions')
    args = parser.parse_args()
    
    upload_to_erp(unread_only=args.unread)