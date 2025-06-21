from fraud_scoring import is_fraudulent

txn = {"amount": 5000, "time": "00:45"}
res = is_fraudulent(txn)

if res.get("is_fraud") is True:
    print("⚠️ Suspicious transaction detected!")
    print("🧮 Fraud score:", res["fraud_score"])
elif res.get("is_fraud") is False:
    print("✅ Transaction looks normal.")
    print("🧮 Fraud score:", res["fraud_score"])
else:
    print("❌ Error:", res.get("error", "Unknown error"))
