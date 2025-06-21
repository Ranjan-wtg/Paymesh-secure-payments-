import json
import sqlite3
import time
from datetime import datetime
from phishing_detector import classify_sms
from fraud_scoring import is_fraudulent
from trust_score import get_trust_score
from sms_controller import SMSController
import hashlib
import bcrypt

class PayMeshRouter:
    def __init__(self):
        self.db_path = "paymesh.db"
        self.sms_controller = SMSController()
        self.current_user = None
        self.failed_attempts = {}
        self.lockout_time = {}
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with enhanced SMS logging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                phone_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Enhanced transactions table with SMS fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                recipient_phone TEXT,
                amount REAL NOT NULL,
                description TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hour INTEGER,
                phishing_flag BOOLEAN DEFAULT FALSE,
                phishing_confidence REAL DEFAULT 0,
                fraud_flag BOOLEAN DEFAULT FALSE,
                fraud_score REAL DEFAULT 0,
                trust_score REAL DEFAULT 1.0,
                risk_factors TEXT,
                transmission_method TEXT DEFAULT 'online',
                sms_file_path TEXT,
                synced BOOLEAN DEFAULT FALSE,
                status TEXT DEFAULT 'pending'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def authenticate_user(self, username, password):
        """Enhanced authentication with lockout protection"""
        # Check lockout
        if username in self.lockout_time:
            if time.time() - self.lockout_time[username] < 60:  # 60 second lockout
                return {
                    'success': False, 
                    'message': f'Account locked. Try again in {60 - int(time.time() - self.lockout_time[username])} seconds.'
                }
            else:
                del self.lockout_time[username]
                del self.failed_attempts[username]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT password_hash, phone_number FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result and bcrypt.checkpw(password.encode('utf-8'), result[0]):
            self.current_user = {
                'username': username,
                'phone_number': result[1]
            }
            # Reset failed attempts on successful login
            if username in self.failed_attempts:
                del self.failed_attempts[username]
            return {'success': True, 'message': 'Login successful', 'user': self.current_user}
        else:
            # Track failed attempts
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            if self.failed_attempts[username] >= 5:
                self.lockout_time[username] = time.time()
                return {'success': False, 'message': 'Too many failed attempts. Account locked for 60 seconds.'}
            
            return {
                'success': False, 
                'message': f'Invalid credentials. {5 - self.failed_attempts[username]} attempts remaining.'
            }
    
    def register_user(self, username, password, phone_number):
        """Enhanced user registration with phone number"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                'INSERT INTO users (username, password_hash, phone_number) VALUES (?, ?, ?)',
                (username, password_hash, phone_number)
            )
            conn.commit()
            return {'success': True, 'message': 'User registered successfully'}
        except sqlite3.IntegrityError:
            return {'success': False, 'message': 'Username already exists'}
        finally:
            conn.close()
    
    def security_pipeline(self, transaction_data):
        """Enhanced security pipeline using correct function signatures"""
        security_results = {
            'phishing': {'safe': True, 'confidence': 0},
            'fraud': {'safe': True, 'score': 0, 'is_fraud': False},
            'trust': {'safe': True, 'score': 1.0, 'risk_factors': []}
        }
        
        # 1. Phishing Detection
        description = transaction_data.get('description', '')
        if description:
            try:
                phishing_result = classify_sms(description)
                security_results['phishing'] = phishing_result
                
                # Handle different return formats
                if isinstance(phishing_result, dict):
                    if not phishing_result.get('safe', True):
                        return {
                            'safe': False,
                            'reason': 'phishing_detected',
                            'details': security_results
                        }
                elif isinstance(phishing_result, str) and 'phishing' in phishing_result.lower():
                    security_results['phishing'] = {'safe': False, 'details': phishing_result}
                    return {
                        'safe': False,
                        'reason': 'phishing_detected',
                        'details': security_results
                    }
            except Exception as e:
                print(f"Phishing detection error: {e}")
        
        # 2. Fraud Detection (using correct is_fraudulent function)
        try:
            # Prepare transaction in correct format
            fraud_txn = {
                "amount": transaction_data.get('amount', 0),
                "time": f"{transaction_data.get('hour', datetime.now().hour):02d}:{datetime.now().minute:02d}"
            }
            
            fraud_result = is_fraudulent(fraud_txn)
            security_results['fraud'] = fraud_result
            
            if fraud_result.get("is_fraud") is True:
                return {
                    'safe': False,
                    'reason': 'fraud_detected',
                    'details': security_results
                }
        except Exception as e:
            print(f"Fraud detection error: {e}")
        
        # 3. Trust Score Analysis (using correct get_trust_score function)
        try:
            # Prepare transaction in correct format
            trust_txn = {
                "amount": transaction_data.get('amount', 0),
                "time": f"{transaction_data.get('hour', datetime.now().hour):02d}:{datetime.now().minute:02d}"
            }
            
            trust_result = get_trust_score(trust_txn)
            security_results['trust'] = trust_result
            
            trust_score = trust_result.get("trust_score", 1.0)
            if trust_score < 0.2:  # Enhanced threshold
                return {
                    'safe': False,
                    'reason': 'low_trust_score',
                    'details': security_results
                }
        except Exception as e:
            print(f"Trust score calculation error: {e}")
        
        return {
            'safe': True,
            'details': security_results
        }
    
    def try_online_transaction(self, transaction_data):
        """Simulate online transaction attempt"""
        # Simulate network check
        import random
        if random.random() > 0.3:  # 70% online success rate
            return {
                'status': 'success',
                'method': 'online',
                'message': 'Transaction completed online'
            }
        return {
            'status': 'failed',
            'method': 'online',
            'message': 'Network unavailable'
        }
    
    def try_bluetooth_transaction(self, transaction_data):
        """Simulate Bluetooth transaction attempt"""
        import random
        if random.random() > 0.5:  # 50% Bluetooth success rate
            return {
                'status': 'success',
                'method': 'bluetooth',
                'message': 'Transaction completed via Bluetooth'
            }
        return {
            'status': 'failed',
            'method': 'bluetooth',
            'message': 'Bluetooth device not found'
        }
    
    def try_sms_transaction(self, transaction_data):
        """Enhanced SMS transaction using corrected SMS controller"""
        try:
            # Ensure recipient phone is available
            if not transaction_data.get('recipient_phone'):
                return {
                    'status': 'failed',
                    'method': 'sms',
                    'message': 'Recipient phone number required for SMS'
                }
            
            # Use SMS controller with corrected functions
            sms_result = self.sms_controller.send_transaction(transaction_data)
            
            if sms_result.get('status') == 'sent':
                return {
                    'status': 'success',
                    'method': 'sms_backend',
                    'message': 'Transaction sent via SMS',
                    'sms_file': sms_result.get('file_path'),
                    'security_scores': sms_result.get('security_scores', {}),
                    'details': sms_result
                }
            elif sms_result.get('status') == 'blocked':
                return {
                    'status': 'blocked',
                    'method': 'sms',
                    'message': f"Transaction blocked: {sms_result.get('reason')}",
                    'security_scores': sms_result.get('security_scores', {}),
                    'details': sms_result
                }
            else:
                return {
                    'status': 'failed',
                    'method': 'sms',
                    'message': f"SMS failed: {sms_result.get('error', 'Unknown error')}",
                    'details': sms_result
                }
                
        except Exception as e:
            return {
                'status': 'failed',
                'method': 'sms',
                'message': f'SMS transaction error: {str(e)}'
            }
    
    def store_local_transaction(self, transaction_data):
        """Enhanced local storage with corrected security data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO transactions (
                    sender, recipient, recipient_phone, amount, description, 
                    hour, phishing_flag, phishing_confidence, fraud_flag, 
                    fraud_score, trust_score, risk_factors, transmission_method, 
                    sms_file_path, synced, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction_data.get('sender', ''),
                transaction_data.get('recipient', ''),
                transaction_data.get('recipient_phone', ''),
                transaction_data.get('amount', 0),
                transaction_data.get('description', ''),
                transaction_data.get('hour', datetime.now().hour),
                transaction_data.get('phishing_flag', False),
                transaction_data.get('phishing_confidence', 0),
                transaction_data.get('fraud_flag', False),
                transaction_data.get('fraud_score', 0),
                transaction_data.get('trust_score', 1.0),
                json.dumps(transaction_data.get('risk_factors', [])),
                'local_storage',
                transaction_data.get('sms_file_path'),
                False,
                'stored_locally'
            ))
            
            conn.commit()
            transaction_id = cursor.lastrowid
            
            return {
                'status': 'success',
                'method': 'local_storage',
                'message': 'Transaction stored locally',
                'transaction_id': transaction_id
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'method': 'local_storage',
                'message': f'Local storage error: {str(e)}'
            }
        finally:
            conn.close()
    
    def enhanced_fallback_chain(self, transaction_data):
        """Enhanced fallback chain with corrected SMS backend"""
        fallback_results = []
        
        # Add current user as sender if not specified
        if not transaction_data.get('sender') and self.current_user:
            transaction_data['sender'] = self.current_user['username']
        
        # Add timestamp and hour if not present
        if not transaction_data.get('timestamp'):
            transaction_data['timestamp'] = datetime.now().isoformat()
        if not transaction_data.get('hour'):
            transaction_data['hour'] = datetime.now().hour
        
        # Try Online Transaction
        print("Attempting online transaction...")
        online_result = self.try_online_transaction(transaction_data)
        fallback_results.append(online_result)
        
        if online_result['status'] == 'success':
            return {
                'final_status': 'success',
                'method': 'online',
                'details': online_result,
                'fallback_chain': fallback_results
            }
        
        # Try Bluetooth Transaction
        print("Online failed. Attempting Bluetooth...")
        bluetooth_result = self.try_bluetooth_transaction(transaction_data)
        fallback_results.append(bluetooth_result)
        
        if bluetooth_result['status'] == 'success':
            return {
                'final_status': 'success',
                'method': 'bluetooth',
                'details': bluetooth_result,
                'fallback_chain': fallback_results
            }
        
        # Try SMS Backend (CORRECTED)
        print("Bluetooth failed. Attempting SMS backend...")
        sms_result = self.try_sms_transaction(transaction_data)
        fallback_results.append(sms_result)
        
        if sms_result['status'] == 'success':
            # Store successful SMS transaction with security data
            transaction_data.update({
                'transmission_method': 'sms_backend',
                'sms_file_path': sms_result.get('sms_file'),
                'status': 'sent_via_sms',
                'fraud_score': sms_result.get('security_scores', {}).get('fraud_score', 0),
                'trust_score': sms_result.get('security_scores', {}).get('trust_score', 1.0),
                'risk_factors': sms_result.get('security_scores', {}).get('risk_factors', [])
            })
            local_storage = self.store_local_transaction(transaction_data)
            
            return {
                'final_status': 'success',
                'method': 'sms_backend',
                'details': sms_result,
                'local_storage': local_storage,
                'fallback_chain': fallback_results
            }
        elif sms_result['status'] == 'blocked':
            return {
                'final_status': 'blocked',
                'method': 'sms_security',
                'details': sms_result,
                'fallback_chain': fallback_results
            }
        
        # Final Fallback: Local Storage
        print("SMS failed. Storing locally...")
        local_result = self.store_local_transaction(transaction_data)
        fallback_results.append(local_result)
        
        return {
            'final_status': 'local_storage',
            'method': 'local_storage',
            'details': local_result,
            'fallback_chain': fallback_results
        }
    
    def process_transaction(self, transaction_data):
        """Main transaction processing with corrected security pipeline"""
        if not self.current_user:
            return {
                'success': False,
                'message': 'User not authenticated'
            }
        
        # Security Pipeline Check using corrected functions
        security_check = self.security_pipeline(transaction_data)
        
        if not security_check['safe']:
            # Extract security data for logging
            fraud_data = security_check['details'].get('fraud', {})
            trust_data = security_check['details'].get('trust', {})
            phishing_data = security_check['details'].get('phishing', {})
            
            # Log blocked transaction with corrected data
            transaction_data.update({
                'status': 'blocked',
                'phishing_flag': security_check['reason'] == 'phishing_detected',
                'phishing_confidence': phishing_data.get('confidence', 0),
                'fraud_flag': fraud_data.get('is_fraud', False),
                'fraud_score': fraud_data.get('fraud_score', 0),
                'trust_score': trust_data.get('trust_score', 1.0),
                'risk_factors': trust_data.get('risk_factors', [])
            })
            self.store_local_transaction(transaction_data)
            
            return {
                'success': False,
                'message': f'Transaction blocked: {security_check["reason"]}',
                'security_details': security_check['details']
            }
        
        # Process through fallback chain
        result = self.enhanced_fallback_chain(transaction_data)
        
        return {
            'success': result['final_status'] in ['success', 'local_storage'],
            'method': result['method'],
            'details': result,
            'message': f'Transaction processed via {result["method"]}'
        }
    
    def process_incoming_sms(self):
        """Process incoming SMS transactions"""
        try:
            incoming_transactions = self.sms_controller.process_inbox()
            processed_count = 0
            
            for transaction in incoming_transactions:
                if transaction['status'] == 'decoded':
                    # Store received transaction
                    txn_data = transaction['transaction_data']
                    txn_data.update({
                        'transmission_method': 'sms_received',
                        'sender': transaction.get('sender', 'unknown'),
                        'status': 'received_via_sms'
                    })
                    
                    self.store_local_transaction(txn_data)
                    processed_count += 1
            
            return {
                'success': True,
                'message': f'Processed {processed_count} incoming SMS transactions'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Error processing incoming SMS: {str(e)}'
            }
    
    def get_unsynced_transactions(self):
        """Get unsynced transactions for later processing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, sender, recipient, amount, description, transmission_method, status
            FROM transactions 
            WHERE synced = FALSE 
            ORDER BY timestamp DESC
        ''')
        
        unsynced = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0], 'sender': row[1], 'recipient': row[2],
                'amount': row[3], 'description': row[4], 
                'method': row[5], 'status': row[6]
            } for row in unsynced
        ]

# Test the corrected system
def test_corrected_router():
    """Test the corrected SMS router system"""
    router = PayMeshRouter()
    
    # Test user registration with phone
    reg_result = router.register_user("test_user", "password123", "+919876543210")
    print(f"Registration: {reg_result}")
    
    # Test authentication
    auth_result = router.authenticate_user("test_user", "password123")
    print(f"Authentication: {auth_result}")
    
    # Test transactions with different risk profiles
    test_transactions = [
        {
            'recipient': 'merchant',
            'recipient_phone': '+919123456789',
            'amount': 100,
            'description': 'Payment for groceries'
        },
        {
            'recipient': 'suspicious_merchant',
            'recipient_phone': '+919999888777',
            'amount': 5000,  # High amount 
            'description': 'Urgent: Your account will be suspended!',  # Phishing
            'hour': 0  # Suspicious time
        }
    ]
    
    for i, transaction in enumerate(test_transactions, 1):
        print(f"\n--- Test Transaction {i} ---")
        result = router.process_transaction(transaction)
        print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test incoming SMS processing
    incoming_result = router.process_incoming_sms()
    print(f"\nIncoming SMS Processing: {incoming_result}")

if __name__ == "__main__":
    test_corrected_router()
