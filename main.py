from pyzkaccess import ZKAccess

import config
from erp_uploader import ERPUploader, filter_events_by_days


def fetch_all_transactions(unread_only: bool = False):
    """Fetch all transactions from all configured devices.
    
    Args:
        unread_only: If True, fetch only unread transactions.
    """
    all_transactions = []
    
    for ip_code in config.config['ip_codes']:
        ip = ip_code['ip']
        code = ip_code['code']
        
        connstr = f'protocol=TCP,ipaddress={ip},port=4370,timeout=4000,passwd={config.config["password"]}'
        
        with ZKAccess(connstr=connstr) as zk:
            query = zk.table('Transaction')
            if unread_only:
                query = query.unread()
            for txn in query:
                txn_dict = txn.dict
                txn_dict['device_code'] = code
                txn_dict['device_ip'] = ip
                all_transactions.append(txn_dict)
    
    return all_transactions


def upload_to_erp():
    """Fetch events from devices and upload to ERP."""
    # Fetch all transactions
    transactions = fetch_all_transactions()
    
    # Convert to events: (card, unix_timestamp)
    events = [(txn['card'], int(txn['time'].timestamp())) for txn in transactions if txn.get('card')]
    
    # Sort by timestamp
    events.sort(key=lambda x: x[1])
    
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
    upload_to_erp()