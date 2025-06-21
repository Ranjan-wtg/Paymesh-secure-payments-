# phishing_detector.py - Your existing phishing detection system

import pickle
import os

# ✅ Path to your trained model
MODEL_PATH = r"D:\The New Data Trio\phishing_svm_model.pkl"

# ✅ Load once
try:
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print("✅ Phishing SVM model loaded successfully")
    MODEL_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Phishing model loading failed: {e}")
    MODEL_AVAILABLE = False
    model = None

def classify_sms(text):
    """
    Returns:
        {
            "is_phishing": True/False,
            "confidence": float (0 to 1),
        }
    """
    if not MODEL_AVAILABLE or model is None:
        # Fallback when model not available
        return {
            "is_phishing": False,
            "confidence": 0.0,
            "error": "Model not available"
        }
    
    try:
        pred = model.decision_function([text])  # distance from hyperplane
        score = pred[0]
        label = model.predict([text])[0]

        # normalize score to 0-1
        confidence = abs(score) / (abs(score) + 1)
        return {
            "is_phishing": bool(label),
            "confidence": round(confidence, 2)
        }
    except Exception as e:
        return {
            "is_phishing": False,
            "confidence": 0.0,
            "error": str(e)
        }

# ✅ Example test
if __name__ == "__main__":
    test_messages = [
        "Your KYC is pending. Click here: http://verify-scam.com",
        "PayMesh: ₹500 sent to 9876543210. TXN: TXN123. Transaction completed securely.",
        "URGENT! Claim your $1000 prize now! Click here immediately!",
        "PayMesh Security: Payment processed safely via encrypted channel."
    ]
    
    print("🚀 Testing Your Phishing Detection Model")
    print("=" * 50)
    
    for i, sms in enumerate(test_messages, 1):
        result = classify_sms(sms)
        print(f"\nTest {i}:")
        print("📩 SMS:", sms)
        print("🚨 Detection:", result)
        risk_level = "HIGH" if result.get('confidence', 0) > 0.7 else "MEDIUM" if result.get('confidence', 0) > 0.3 else "LOW"
        print(f"🔍 Risk Level: {risk_level}")
