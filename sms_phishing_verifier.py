# sms_phishing_verifier.py - Updated to use your existing phishing model

import json
import time
from datetime import datetime
from pathlib import Path

# Import your actual phishing detector
from phishing_detector import classify_sms, MODEL_AVAILABLE

class SMSPhishingVerifier:
    def __init__(self):
        self.verification_log = Path("sms_verification_log.json")
        self.phishing_threshold = 0.4  # Adjust based on your model performance
        
        print(f"📱 SMS Phishing Verifier initialized. Model available: {MODEL_AVAILABLE}")
    
    def generate_payment_sms(self, amount, recipient, sender, txn_id):
        """Generate SMS templates for payment verification"""
        templates = {
            "payment_notification": f"PayMesh: You are sending ₹{amount} to {recipient}. TXN: {txn_id}. Confirm to proceed.",
            "security_alert": f"PayMesh Security: ₹{amount} transfer to {recipient} initiated. TXN: {txn_id}. Contact support if unauthorized.",
            "confirmation_request": f"PayMesh: Confirm payment - Send ₹{amount} to {recipient}? Reply YES to confirm. TXN: {txn_id}",
            "success_notification": f"PayMesh: Payment successful - ₹{amount} sent to {recipient}. TXN: {txn_id}. Secure transaction completed."
        }
        return templates
    
    def verify_payment_sms_security(self, amount, recipient, sender, txn_id):
        """Comprehensive SMS phishing verification using your trained SVM model"""
        verification_result = {
            "payment_approved": False,
            "phishing_risk": "UNKNOWN",
            "risk_score": 0.0,
            "blocked_reason": None,
            "sms_templates_checked": [],
            "verification_details": {},
            "model_status": "active" if MODEL_AVAILABLE else "unavailable"
        }
        
        try:
            # Check if your model is available
            if not MODEL_AVAILABLE:
                verification_result["payment_approved"] = True  # Allow if model unavailable
                verification_result["phishing_risk"] = "UNKNOWN"
                verification_result["blocked_reason"] = "Phishing model unavailable - payment allowed"
                print("⚠️ Phishing model not available, allowing payment")
                return verification_result
            
            # Generate all SMS templates that would be sent
            sms_templates = self.generate_payment_sms(amount, recipient, sender, txn_id)
            
            highest_risk = 0.0
            most_risky_template = None
            template_results = {}
            
            print(f"🔍 Checking {len(sms_templates)} SMS templates for phishing...")
            
            # Check each SMS template using your SVM model
            for template_type, sms_content in sms_templates.items():
                phishing_result = classify_sms(sms_content)
                
                # Handle error cases
                if "error" in phishing_result:
                    print(f"⚠️ Error checking template '{template_type}': {phishing_result['error']}")
                    continue
                
                phishing_score = phishing_result.get("confidence", 0)
                is_phishing = phishing_result.get("is_phishing", False)
                
                template_results[template_type] = {
                    "sms_content": sms_content,
                    "phishing_score": phishing_score,
                    "is_phishing": is_phishing,
                    "risk_level": self._calculate_risk_level(phishing_score),
                    "svm_decision": "PHISHING" if is_phishing else "LEGITIMATE"
                }
                
                # Track highest risk
                if phishing_score > highest_risk:
                    highest_risk = phishing_score
                    most_risky_template = template_type
                
                print(f"  📄 {template_type}: {'🚨 PHISHING' if is_phishing else '✅ SAFE'} (score: {phishing_score:.3f})")
            
            verification_result["sms_templates_checked"] = list(sms_templates.keys())
            verification_result["verification_details"] = template_results
            verification_result["risk_score"] = highest_risk
            
            # Payment approval logic using your SVM model's output
            if highest_risk > self.phishing_threshold:
                verification_result["payment_approved"] = False
                verification_result["phishing_risk"] = "HIGH"
                verification_result["blocked_reason"] = f"SMS template '{most_risky_template}' flagged as phishing by SVM model (confidence: {highest_risk:.3f})"
                print(f"❌ Payment BLOCKED: {verification_result['blocked_reason']}")
            else:
                verification_result["payment_approved"] = True
                verification_result["phishing_risk"] = "LOW"
                verification_result["blocked_reason"] = None
                print(f"✅ Payment APPROVED: All SMS templates passed SVM phishing check (max risk: {highest_risk:.3f})")
            
            # Log verification
            self._log_verification(amount, recipient, sender, txn_id, verification_result)
            
            return verification_result
            
        except Exception as e:
            verification_result["payment_approved"] = False
            verification_result["blocked_reason"] = f"SMS verification system error: {str(e)}"
            verification_result["phishing_risk"] = "ERROR"
            print(f"❌ SMS verification error: {e}")
            return verification_result
    
    def _calculate_risk_level(self, phishing_score):
        """Calculate human-readable risk level based on SVM confidence"""
        if phishing_score > 0.8:
            return "CRITICAL"
        elif phishing_score > 0.6:
            return "HIGH"
        elif phishing_score > 0.3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _log_verification(self, amount, recipient, sender, txn_id, verification_result):
        """Log SMS verification results for audit trail"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "transaction": {
                "amount": amount,
                "recipient": recipient,
                "sender": sender,
                "txn_id": txn_id
            },
            "verification_result": verification_result,
            "model_info": {
                "model_type": "SVM",
                "model_available": MODEL_AVAILABLE,
                "threshold_used": self.phishing_threshold
            }
        }
        
        # Append to verification log
        logs = []
        if self.verification_log.exists():
            try:
                with open(self.verification_log, 'r') as f:
                    logs = json.load(f)
            except:
                logs = []
        
        logs.append(log_entry)
        
        with open(self.verification_log, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def get_verification_statistics(self):
        """Get SMS verification statistics"""
        if not self.verification_log.exists():
            return {
                "total_verifications": 0, 
                "approvals": 0, 
                "blocks": 0,
                "model_status": "active" if MODEL_AVAILABLE else "unavailable"
            }
        
        try:
            with open(self.verification_log, 'r') as f:
                logs = json.load(f)
            
            total = len(logs)
            approved = sum(1 for log in logs if log["verification_result"]["payment_approved"])
            blocked = total - approved
            
            # Calculate average risk scores
            risk_scores = [log["verification_result"]["risk_score"] for log in logs if log["verification_result"]["risk_score"] > 0]
            avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
            
            return {
                "total_verifications": total,
                "approvals": approved,
                "blocks": blocked,
                "approval_rate": (approved / total * 100) if total > 0 else 0,
                "average_risk_score": round(avg_risk, 3),
                "model_status": "active" if MODEL_AVAILABLE else "unavailable",
                "model_type": "SVM"
            }
        except:
            return {"total_verifications": 0, "approvals": 0, "blocks": 0}

# Global SMS phishing verifier using your SVM model
sms_phishing_verifier = SMSPhishingVerifier()
