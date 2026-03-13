import argparse
import logging
import config
from typing import List
from pyzkaccess import ZKAccess
from config import validate_config
from erp_uploader import ERPUploader, filter_events_by_days
from models import Event

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def fetch_employees_from_device(zk: ZKAccess) -> List[str]:
    """Fetch all card numbers from a single device.
    Args:
        zk: ZKAccess connection instance
    Returns:
        List of card numbers
    """
    cards = {}
    for user in zk.table('User'):
        user_dict = user.dict
        if user_dict.get('card'):
            cards[str(user_dict['card'])] = True
    return list(cards.keys())


def fetch_all_employees() -> List[str]:
    """Fetch all card numbers from all configured devices.

    Returns:
        List of card numbers from all devices
    """
    all_cards = {}

    for ip_config in config.config['ip_codes']:
        ip = ip_config['ip']
        origin_id = ip_config['origin_id']
        
        # Only fetch users from Timeformers (origin_id = 0)
        if origin_id != 0:
            continue

        connstr = f'protocol=TCP,ipaddress={ip},port=4370,timeout=4000,passwd={config.config["password"]}'

        try:
            with ZKAccess(connstr=connstr) as zk:
                cards = fetch_employees_from_device(zk, origin_id)
                for card in cards:
                    all_cards[card] = True
                logger.info(f"Fetched {len(cards)} cards from device {ip}")
        except Exception as e:
            logger.error(f"Failed to fetch employees from device {ip}: {e}")

    return list(all_cards.keys())


def fetch_all_transactions(unread_only: bool = False) -> List[dict]:
    """Fetch all transactions from all configured devices.

    Args:
        unread_only: If True, fetch only unread transactions.

    Returns:
        List of transaction dictionaries
    """
    all_transactions = []

    for ip_config in config.config['ip_codes']:
        ip = ip_config['ip']
        origin_id = ip_config['origin_id']

        connstr = f'protocol=TCP,ipaddress={ip},port=4370,timeout=4000,passwd={config.config["password"]}'

        try:
            with ZKAccess(connstr=connstr) as zk:
                query = zk.table('Transaction')
                if unread_only:
                    query = query.unread()
                for txn in query:
                    txn_dict = txn.dict
                    txn_dict['device_ip'] = ip
                    txn_dict['origin_id'] = origin_id
                    all_transactions.append(txn_dict)
        except Exception as e:
            logger.error(f"Failed to fetch transactions from device {ip}: {e}")

    return all_transactions


def upload_to_erp(unread_only: bool = False, days: int = 30):
    """Fetch events from devices and upload to ERP.

    Args:
        unread_only: If True, fetch only unread transactions.
        days: Number of days to filter events (default: 30)
    """
    employee_cards = fetch_all_employees()
    logger.info(f"Total employees: {len(employee_cards)}")

    transactions = fetch_all_transactions(unread_only=unread_only)

    events = [
        Event(
            card=txn['card'],
            timestamp=int(txn['time'].timestamp()),
            origin_id=txn['origin_id'],
        )
        for txn in transactions
        if txn.get('card')
    ]

    events.sort(key=lambda e: e.timestamp)

    events = filter_events_by_days(events, days=days)
    logger.info(f"Total events (last {days} days): {len(events)}")

    uploader = ERPUploader(
        base_url=config.config['erp_base_url'],
        email=config.config['erp_login'],
        password=config.config['erp_password'],
    )

    uploader.login()
    uploader.upload_events(employee_cards, events)


def main():
    validate_config()

    parser = argparse.ArgumentParser(description='Sync attendance data to ERP')
    parser.add_argument('--unread', action='store_true', help='Fetch only unread transactions')
    parser.add_argument('--days', type=int, default=30, help='Number of days to filter events (default: 30)')
    args = parser.parse_args()
    
    upload_to_erp(unread_only=args.unread, days=args.days)


if __name__ == '__main__':
    main()