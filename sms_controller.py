import os
import json
import sys
import traceback
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sms_backend import SMSBackendService
from phishing_detector import classify_sms
from fraud_scoring import is_fraudulent
from trust_score import get_trust_score

class SMSController:
    def __init__(self):
        self.sms_backend = SMSBackendService()
        self.transaction_log = "sms_transactions.json"
    
    def send_transaction(self, transaction_data):
        """Main SMS transaction sending with security pipeline using correct functions"""
        
        try:
            # Security Pipeline using your actual functions
            
            # 1. Phishing Detection (using your classify_sms function)
            description = transaction_data.get('description', '')
            if description:
                try:
                    phishing_result = classify_sms(description)
                    print(f"Phishing check result: {phishing_result}")
                    
                    # Handle different return formats from your phishing detector
                    if isinstance(phishing_result, dict):
                        if not phishing_result.get('safe', True):
                            return {
                                'status': 'blocked',
                                'reason': 'phishing_detected',
                                'confidence': phishing_result.get('confidence', 0),
                                'details': phishing_result
                            }
                    elif isinstance(phishing_result, str) and 'phishing' in phishing_result.lower():
                        return {
                            'status': 'blocked',
                            'reason': 'phishing_detected',
                            'details': phishing_result
                        }
                        
                except Exception as e:
                    print(f"Phishing detection error: {e}")
                    # Continue with transaction if phishing detection fails
            
            # 2. Fraud Detection (using your is_fraudulent function)
            try:
                # Prepare transaction for your fraud model format
                fraud_txn = {
                    "amount": transaction_data.get('amount', 0),
                    "time": f"{transaction_data.get('hour', datetime.now().hour):02d}:{datetime.now().minute:02d}"
                }
                
                fraud_result = is_fraudulent(fraud_txn)
                print(f"Fraud check result: {fraud_result}")
                
                if fraud_result.get("is_fraud") is True:
                    return {
                        'status': 'blocked',
                        'reason': 'fraud_detected',
                        'fraud_score': fraud_result.get("fraud_score", 0),
                        'details': fraud_result
                    }
                elif fraud_result.get("error"):
                    print(f"Fraud detection error: {fraud_result.get('error')}")
                    # Continue with transaction if fraud detection fails
                    
            except Exception as e:
                print(f"Fraud detection error: {e}")
                # Continue with transaction if fraud detection fails
            
            # 3. Trust Score Check (using your get_trust_score function)
            try:
                # Prepare transaction for your trust score format
                trust_txn = {
                    "amount": transaction_data.get('amount', 0),
                    "time": f"{transaction_data.get('hour', datetime.now().hour):02d}:{datetime.now().minute:02d}"
                }
                
                trust_result = get_trust_score(trust_txn)
                print(f"Trust score result: {trust_result}")
                
                trust_score = trust_result.get("trust_score", 1.0)
                risk_factors = trust_result.get("risk_factors", [])
                
                if trust_score < 0.3:
                    return {
                        'status': 'blocked',
                        'reason': 'low_trust_score',
                        'trust_score': trust_score,
                        'risk_factors': risk_factors,
                        'details': trust_result
                    }
                    
            except Exception as e:
                print(f"Trust score calculation error: {e}")
                trust_score = 1.0  # Default to safe if calculation fails
                risk_factors = []
            
            # All security checks passed - send via SMS Backend
            result = self.sms_backend.send_transaction_sms(
                transaction_data.get('recipient_phone', ''),
                transaction_data
            )
            
            # Add security scores to result
            result['security_scores'] = {
                'trust_score': trust_score,
                'risk_factors': risk_factors,
                'fraud_score': fraud_result.get("fraud_score", 0) if 'fraud_result' in locals() else 0
            }
            
            # Log transaction
            self._log_transaction(transaction_data, result)
            return result
            
        except Exception as e:
            print(f"SMS Controller error: {e}")
            print(traceback.format_exc())
            return {
                'status': 'failed',
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    def process_inbox(self):
        """Process all incoming SMS files"""
        try:
            inbox_dir = self.sms_backend.sms_inbox
            processed_transactions = []
            
            if not os.path.exists(inbox_dir):
                return processed_transactions
            
            for sms_file in os.listdir(inbox_dir):
                if sms_file.endswith('.sms'):
                    file_path = os.path.join(inbox_dir, sms_file)
                    try:
                        result = self.sms_backend.process_incoming_sms(file_path)
                        
                        if result['status'] == 'decoded':
                            processed_transactions.append(result)
                            # Move processed file
                            processed_path = f"{file_path}.processed"
                            os.rename(file_path, processed_path)
                            print(f"Processed SMS file: {sms_file}")
                            
                    except Exception as e:
                        print(f"Error processing SMS file {sms_file}: {e}")
                        continue
            
            return processed_transactions
            
        except Exception as e:
            print(f"Error processing inbox: {e}")
            return []
    
    def _log_transaction(self, transaction_data, result):
        """Log SMS transaction with error handling"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'transaction_timestamp': transaction_data.get('timestamp', ''),
                'sender': transaction_data.get('sender', ''),
                'recipient': transaction_data.get('recipient', ''),
                'recipient_phone': transaction_data.get('recipient_phone', ''),
                'amount': transaction_data.get('amount', 0),
                'description': transaction_data.get('description', ''),
                'status': result.get('status', 'unknown'),
                'method': 'sms',
                'security_scores': result.get('security_scores', {}),
                'sms_file_path': result.get('file_path', '')
            }
            
            # Load existing logs
            if os.path.exists(self.transaction_log):
                try:
                    with open(self.transaction_log, 'r') as f:
                        logs = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    logs = []
            else:
                logs = []
            
            logs.append(log_entry)
            
            # Save updated logs
            with open(self.transaction_log, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            print(f"Error logging transaction: {e}")

# Test function using your step-by-step approach
def test_sms_controller():
    """Test SMS controller with your actual function signatures"""
    print("Testing SMS Controller with correct functions...")
    
    # Initialize controller
    sms_controller = SMSController()
    
    # Test transaction data matching your function formats
    test_transactions = [
        {
            'sender': 'test_user',
            'recipient': 'merchant',
            'recipient_phone': '+919876543210',
            'amount': 100,
            'description': 'Payment for groceries',
            'timestamp': datetime.now().isoformat(),
            'hour': datetime.now().hour
        },
        {
            'sender': 'test_user', 
            'recipient': 'suspicious_merchant',
            'recipient_phone': '+919123456789',
            'amount': 5000,  # High amount to trigger fraud detection
            'description': 'Urgent: Your account will be suspended. Pay immediately!',  # Phishing attempt
            'timestamp': datetime.now().isoformat(),
            'hour': 0  # Suspicious hour (00:XX)
        },
        {
            'sender': 'test_user',
            'recipient': 'late_merchant', 
            'recipient_phone': '+919999888777',
            'amount': 18000,  # Very high amount
            'description': 'Late night payment',
            'timestamp': datetime.now().isoformat(),
            'hour': 1  # Very suspicious hour (01:XX)
        }
    ]
    
    # Test each transaction
    for i, transaction in enumerate(test_transactions, 1):
        print(f"\n--- Test Transaction {i} ---")
        print(f"Amount: ₹{transaction['amount']}")
        print(f"Hour: {transaction['hour']}:XX")
        print(f"Description: {transaction['description']}")
        
        result = sms_controller.send_transaction(transaction)
        print(f"Result: {json.dumps(result, indent=2)}")
        
        # Show expected behavior
        if result['status'] == 'blocked':
            print(f"⚠️  Transaction blocked: {result['reason']}")
        elif result['status'] == 'sent':
            print("✅ Transaction sent successfully")
    
    # Test inbox processing
    print("\n--- Testing Inbox Processing ---")
    inbox_result = sms_controller.process_inbox()
    print(f"Processed {len(inbox_result)} incoming SMS transactions")
    
    print("\nSMS Controller testing completed!")

if __name__ == "__main__":
    test_sms_controller()
