from ledger import log_transaction
from datetime import datetime

txn = {
    "amount": 5000,
    "to_user": "1234567890",
    "time": datetime.now().strftime("%H:%M"),
    "channel": "Bluetooth",
    "is_fraud": 0,
    "is_phishing": 0,
    "status": "Success",
    "flags": []
}

log_transaction(txn)
