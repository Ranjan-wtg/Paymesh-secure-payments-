import json
import base64
import time
import os
from datetime import datetime
from typing import Dict, Any

class SMSBackendService:
    def __init__(self):
        self.sms_outbox = "sms_outbox/"
        self.sms_inbox = "sms_inbox/"
        self.offline_queue = []
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create SMS directories if they don't exist"""
        os.makedirs(self.sms_outbox, exist_ok=True)
        os.makedirs(self.sms_inbox, exist_ok=True)
    
    def send_transaction_sms(self, recipient_phone: str, transaction_data: Dict) -> Dict[str, Any]:
        """Send transaction via SMS backend"""
        try:
            # Compress transaction data
            compressed_data = base64.b64encode(
                json.dumps(transaction_data).encode()
            ).decode()
            
            sms_payload = f"PMesh:{compressed_data}"
            
            # Write to outbox file (simulating SMS send)
            sms_file = f"{self.sms_outbox}/{recipient_phone}_{int(time.time())}.sms"
            with open(sms_file, 'w') as f:
                json.dump({
                    'recipient': recipient_phone,
                    'message': sms_payload,
                    'timestamp': datetime.now().isoformat(),
                    'transaction_data': transaction_data
                }, f, indent=2)
            
            return {
                'status': 'sent',
                'method': 'file_sms',
                'file_path': sms_file
            }
            
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def process_incoming_sms(self, sms_file_path: str) -> Dict[str, Any]:
        """Process incoming SMS from inbox"""
        try:
            with open(sms_file_path) as f:
                sms_data = json.load(f)
            
            message = sms_data.get('message', '')
            if message.startswith('PMesh:'):
                # Decode transaction
                encoded_data = message[6:]  # Remove "PMesh:"
                decoded_data = json.loads(
                    base64.b64decode(encoded_data.encode()).decode()
                )
                
                return {
                    'status': 'decoded',
                    'transaction_data': decoded_data,
                    'sender': sms_data.get('sender', 'unknown')
                }
            
            return {'status': 'ignored', 'reason': 'not_paymesh_sms'}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
