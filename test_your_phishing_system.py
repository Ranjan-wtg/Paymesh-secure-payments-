# test_your_phishing_system.py - Test with your actual SVM model

from phishing_detector import classify_sms, MODEL_AVAILABLE
from sms_phishing_verifier import sms_phishing_verifier

def test_your_complete_system():
    print("🚀 Testing PayMesh SMS Security with Your SVM Model")
    print("=" * 60)
    
    print(f"📊 Model Status: {'✅ Available' if MODEL_AVAILABLE else '❌ Not Available'}")
    
    # Test 1: Your original phishing detection
    print("\n1. Testing Your Original Phishing Detection:")
    test_messages = [
        "Your KYC is pending. Click here: http://verify-scam.com",
        "PayMesh: ₹500 sent to 9876543210. TXN: TXN123. Transaction completed securely.",
        "URGENT! Claim your $1000 prize now! Click here immediately!",
        "PayMesh Security: Payment processed safely via encrypted channel."
    ]
    
    for i, sms in enumerate(test_messages, 1):
        result = classify_sms(sms)
        print(f"\nTest {i}:")
        print(f"📩 SMS: {sms[:50]}...")
        print(f"🚨 Detection: {result}")
    
    # Test 2: SMS verification for actual payment
    print("\n" + "="*60)
    print("2. Testing SMS Verification for Payment Transaction:")
    
    verification_result = sms_phishing_verifier.verify_payment_sms_security(
        amount=1500,
        recipient="9876543210", 
        sender="testuser",
        txn_id="TXN_DEMO_456"
    )
    
    print(f"\n📊 VERIFICATION RESULTS:")
    print(f"Payment Approved: {'✅ YES' if verification_result['payment_approved'] else '❌ NO'}")
    print(f"Risk Score: {verification_result['risk_score']:.3f}/1.0")
    print(f"Risk Level: {verification_result['phishing_risk']}")
    print(f"Templates Checked: {len(verification_result['sms_templates_checked'])}")
    
    if verification_result['blocked_reason']:
        print(f"Block Reason: {verification_result['blocked_reason']}")
    
    # Show detailed template analysis
    print(f"\n🔍 DETAILED TEMPLATE ANALYSIS:")
    for template_name, details in verification_result['verification_details'].items():
        print(f"  📄 {template_name}:")
        print(f"    SVM Decision: {details['svm_decision']}")
        print(f"    Confidence: {details['phishing_score']:.3f}")
        print(f"    Risk Level: {details['risk_level']}")
    
    # Test 3: Statistics
    print(f"\n" + "="*60)
    print("3. SMS Verification Statistics:")
    stats = sms_phishing_verifier.get_verification_statistics()
    print(f"Model Type: {stats.get('model_type', 'Unknown')}")
    print(f"Model Status: {stats.get('model_status', 'unknown')}")
    print(f"Total Verifications: {stats['total_verifications']}")
    if stats['total_verifications'] > 0:
        print(f"Approval Rate: {stats.get('approval_rate', 0):.1f}%")
        print(f"Average Risk Score: {stats.get('average_risk_score', 0):.3f}")

if __name__ == "__main__":
    test_your_complete_system()
