# twilio_sms_sender.py - Twilio SMS with hardcoded credentials for demo

import os
from datetime import datetime
import json
from pathlib import Path

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
    print("✅ Twilio library available")
except ImportError:
    print("⚠️ Twilio library not found. Install with: pip install twilio")
    TWILIO_AVAILABLE = False

# Import your existing phishing detector
try:
    from phishing_detector import classify_sms
    PHISHING_DETECTION_AVAILABLE = True
except ImportError:
    print("⚠️ Phishing detector not available - using basic detection")
    PHISHING_DETECTION_AVAILABLE = False

class TwilioSMSSender:
    def __init__(self):
        # ============ HARDCODED CREDENTIALS FOR DEMO ============
        # TODO: Replace with your actual Twilio credentials
        # Get free trial account at: https://www.twilio.com/try-twilio
        
        self.account_sid = "ACe87d5fffca7a1e77435c365f06d68c94"  # Your Account SID
        self.auth_token = "20c7bc8d941a254a69b69bf923185121"              # Your Auth Token  
        self.twilio_number = "+19124205557"  # Your Twilio Phone Number
        
        # ======================================================
        # SECURITY NOTE: For production, use environment variables:
        # self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        # self.auth_token = os.getenv('TWILIO_AUTH_TOKEN') 
        # self.twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
        # ======================================================
        
        self.client = None
        self.sms_available = False
        
        if TWILIO_AVAILABLE and self.account_sid.startswith("AC"):
            try:
                self.client = Client(self.account_sid, self.auth_token)
                # Test the connection
                self.client.api.accounts(self.account_sid).fetch()
                self.sms_available = True
                print("✅ Twilio SMS service initialized successfully")
                print(f"📱 Using Twilio number: {self.twilio_number}")
            except Exception as e:
                print(f"⚠️ Twilio initialization failed: {e}")
                print("💡 Check your Account SID, Auth Token, and Phone Number")
                self.sms_available = False
        else:
            print("⚠️ Twilio credentials not configured - using simulation mode")
            print("💡 Update the hardcoded credentials in __init__ method")
            self.sms_available = False
        
        # Create SMS log directory
        self.log_dir = Path("sms_logs")
        self.log_dir.mkdir(exist_ok=True)
    
    def send_secure_sms(self, to_number, message, transaction_data=None):
        """Send SMS with security checks via Twilio"""
        
        # Step 1: Security check
        security_check = self.check_sms_security(message)
        
        if not security_check["safe_to_send"]:
            return {
                "success": False,
                "error": "SMS blocked by security scan",
                "reason": security_check["reason"],
                "phishing_score": security_check["phishing_score"]
            }
        
        # Step 2: Send via Twilio or simulate
        if self.sms_available:
            return self._send_real_sms(to_number, message, transaction_data, security_check)
        else:
            return self._simulate_sms(to_number, message, transaction_data, security_check)
    
    def _send_real_sms(self, to_number, message, transaction_data, security_check):
        """Send actual SMS via Twilio"""
        try:
            print(f"📱 Sending real SMS via Twilio to {to_number}...")
            print(f"📄 Message: {message[:50]}..." if len(message) > 50 else f"📄 Message: {message}")
            
            twilio_message = self.client.messages.create(
                body=message,
                from_=self.twilio_number,
                to=to_number
            )
            
            # Log successful send
            self._log_sms_activity(to_number, message, "sent", twilio_message.sid, security_check, transaction_data)
            
            print(f"✅ SMS sent successfully via Twilio")
            print(f"   Message SID: {twilio_message.sid}")
            print(f"   Status: {twilio_message.status}")
            
            return {
                "success": True,
                "message_sid": twilio_message.sid,
                "provider": "twilio",
                "phishing_score": security_check["phishing_score"],
                "status": "sent",
                "twilio_status": twilio_message.status
            }
            
        except Exception as e:
            print(f"❌ Twilio SMS failed: {e}")
            print("💡 Common issues:")
            print("   - Check if phone number is verified (trial accounts)")
            print("   - Ensure phone number format: +1234567890")
            print("   - Verify account has sufficient balance")
            
            return {
                "success": False,
                "error": f"Twilio SMS failed: {str(e)}",
                "provider": "twilio",
                "troubleshooting": "Check credentials and phone number format"
            }
    
    def _simulate_sms(self, to_number, message, transaction_data, security_check):
        """Simulate SMS when Twilio not available"""
        print(f"📱 Simulating SMS to {to_number} (Twilio not configured)")
        print(f"📄 Would send: {message}")
        
        # Simulate delivery
        import random
        import time
        time.sleep(1)  # Simulate network delay
        
        message_id = f"SIM_{int(time.time() * 1000)}"
        delivery_success = random.random() < 0.95  # 95% success rate
        
        if delivery_success:
            self._log_sms_activity(to_number, message, "simulated", message_id, security_check, transaction_data)
            
            print(f"✅ SMS simulation successful")
            return {
                "success": True,
                "message_id": message_id,
                "provider": "simulation",
                "phishing_score": security_check["phishing_score"],
                "status": "simulated"
            }
        else:
            print(f"❌ SMS simulation failed")
            return {
                "success": False,
                "error": "Simulated network failure",
                "provider": "simulation"
            }
    
    def check_sms_security(self, message_text):
        """Check SMS for phishing using your ML model"""
        
        if PHISHING_DETECTION_AVAILABLE:
            try:
                result = classify_sms(message_text)
                phishing_score = result.get("confidence", 0)
                is_phishing = result.get("is_phishing", False)
                
                if is_phishing and phishing_score > 0.7:
                    return {
                        "safe_to_send": False,
                        "reason": "High phishing risk detected by ML model",
                        "phishing_score": phishing_score
                    }
                elif phishing_score > 0.4:
                    return {
                        "safe_to_send": False,
                        "reason": "Medium phishing risk - manual review required",
                        "phishing_score": phishing_score
                    }
                else:
                    return {
                        "safe_to_send": True,
                        "phishing_score": phishing_score,
                        "status": "ML scan passed"
                    }
            except Exception as e:
                print(f"ML phishing detection failed: {e}")
        
        # Fallback to basic detection
        return self._basic_phishing_check(message_text)
    
    def _basic_phishing_check(self, text):
        """Basic phishing pattern detection"""
        phishing_patterns = [
            "click here", "urgent action", "verify account", "suspended",
            "winner", "congratulations", "claim prize", "limited time",
            "suspicious activity", "update payment", "confirm identity"
        ]
        
        found_patterns = [p for p in phishing_patterns if p in text.lower()]
        phishing_score = min(1.0, len(found_patterns) * 0.25)
        
        return {
            "safe_to_send": len(found_patterns) < 2,
            "reason": f"Found {len(found_patterns)} suspicious patterns" if found_patterns else "Basic scan passed",
            "phishing_score": phishing_score,
            "blocked_patterns": found_patterns
        }
    
    def _log_sms_activity(self, phone_number, content, direction, message_id, security_info, transaction_data):
        """Log SMS activity"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "phone_number": phone_number,
            "direction": direction,
            "content": content,
            "message_id": message_id,
            "phishing_score": security_info.get("phishing_score", 0),
            "safe_to_send": security_info.get("safe_to_send", True),
            "transaction_data": transaction_data,
            "provider": "twilio" if self.sms_available else "simulation"
        }
        
        log_file = self.log_dir / f"sms_log_{datetime.now().strftime('%Y-%m-%d')}.json"
        
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(log_entry)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def create_transaction_sms(self, amount, recipient, sender, txn_id, message_type="success"):
        """Create transaction SMS messages"""
        templates = {
            "success": f"PayMesh: ₹{amount} sent to {recipient} successfully. TXN: {txn_id}. Secure offline payment completed.",
            "notification": f"PayMesh: You received ₹{amount} from {sender}. TXN: {txn_id}. Funds will sync when online.",
            "security_alert": f"PayMesh Security: Suspicious transaction of ₹{amount} blocked. TXN: {txn_id}. If legitimate, contact support.",
            "confirmation": f"PayMesh: Confirm ₹{amount} transfer to {recipient}? Reply YES to proceed. TXN: {txn_id}"
        }
        return templates.get(message_type, templates["success"])
    
    def setup_credentials(self, account_sid, auth_token, phone_number):
        """Helper method to set up credentials programmatically"""
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.twilio_number = phone_number
        
        # Reinitialize client
        if TWILIO_AVAILABLE:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                self.client.api.accounts(self.account_sid).fetch()
                self.sms_available = True
                print("✅ Twilio credentials updated successfully")
            except Exception as e:
                print(f"❌ Credential update failed: {e}")
                self.sms_available = False

# Global Twilio SMS sender
twilio_sms_sender = TwilioSMSSender()
