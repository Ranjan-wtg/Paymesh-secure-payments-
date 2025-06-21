from sms_controller import SMSController
from datetime import datetime

def route_transaction_via_sms(transaction_data):
    """Enhanced SMS routing function for your txn_router.py"""
    
    # Initialize SMS controller
    sms_controller = SMSController()
    
    # Add timestamp if not present
    if 'timestamp' not in transaction_data:
        transaction_data['timestamp'] = datetime.now().isoformat()
    
    # Add hour for fraud detection
    if 'hour' not in transaction_data:
        transaction_data['hour'] = datetime.now().hour
    
    # Send transaction
    result = sms_controller.send_transaction(transaction_data)
    
    return result

def process_incoming_sms_transactions():
    """Process incoming SMS transactions"""
    sms_controller = SMSController()
    return sms_controller.process_inbox()

# Test function
def test_sms_transaction():
    """Test SMS functionality"""
    test_transaction = {
        'recipient_phone': '+919876543210',
        'sender': 'test_user',
        'amount': 100,
        'description': 'Payment for groceries',
        'timestamp': datetime.now().isoformat(),
        'hour': datetime.now().hour
    }
    
    result = route_transaction_via_sms(test_transaction)
    print(f"SMS Transaction Result: {result}")
    
    # Process any incoming SMS
    incoming = process_incoming_sms_transactions()
    print(f"Incoming SMS Transactions: {incoming}")

if __name__ == "__main__":
    test_sms_transaction()
