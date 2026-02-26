from pyzkaccess import ZKAccess

import config


def fetch_all_transactions():
    """Fetch all transactions from all configured devices."""
    all_transactions = []
    
    for ip_code in config.config['ip_codes']:
        ip = ip_code['ip']
        code = ip_code['code']
        
        connstr = f'protocol=TCP,ipaddress={ip},port=4370,timeout=4000,passwd={config.config["password"]}'
        
        with ZKAccess(connstr=connstr) as zk:
            transactions = zk.table('Transaction')
            for txn in transactions:
                txn_dict = txn.dict
                txn_dict['device_code'] = code
                txn_dict['device_ip'] = ip
                all_transactions.append(txn_dict)
    
    return all_transactions


if __name__ == '__main__':
    transactions = fetch_all_transactions()
    print(f"Fetched {len(transactions)} transactions")
    for txn in transactions[:5]:  # Print first 5 as sample
        print(txn)