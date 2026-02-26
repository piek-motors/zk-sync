from pyzkaccess import ZKAccess

import config


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


if __name__ == '__main__':
    transactions = fetch_all_transactions()
    
    # Convert to events: (card, unix_timestamp)
    events = [(txn['card'], int(txn['time'].timestamp())) for txn in transactions if txn.get('card')]
    
    # Sort events by timestamp
    events.sort(key=lambda x: x[1])
    
    # Show last 5 events
    print(f"Total events: {len(events)}")
    print("Last 5 events:")
    for card, timestamp in events[-5:]:
        print(f"  Card: {card}, Timestamp: {timestamp}")