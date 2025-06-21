from phishing_detector import classify_sms

sms_text = "Dear customer, update your KYC to avoid suspension."  # From actual app, or test string
result = classify_sms(sms_text)

if result["is_phishing"]:
    print("🚨 Phishing Detected!")
    print(f"🔍 Confidence Score: {result['confidence']}")
    # Optional: Add audio alert
    # voice("Phishing detected. Transaction aborted.")
    # abort_transaction()
else:
    print("✅ SMS is clean. Proceed.")
    print(f"✅ Confidence Score: {result['confidence']}")
