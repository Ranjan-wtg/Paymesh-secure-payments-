from datetime import datetime
from phishing_detector import classify_sms
from fraud_scoring import is_fraudulent_kmeans
from ledger import log_transaction, fetch_unsynced_txns
import requests

# -----------------------------
# 🧠 Fallback Check Functions (Mocked)
# -----------------------------
def check_network():
    return True  # 🔁 Toggle to False to simulate offline

def check_bluetooth():
    return True  # Simulate BT fallback

def check_sms():
    return True  # Simulate SMS fallback

# -----------------------------
# 🔁 Sync with Flask Server
# -----------------------------
def sync_unsynced_txns():
    txns = fetch_unsynced_txns()
    print(f"\n🌐 Attempting to sync {len(txns)} unsynced txns...")

    for row in txns:
        txn_id = row[0]  # first column is id
        data = {"id": txn_id}
        try:
            res = requests.post("http://127.0.0.1:5000/sync", json=data)
            if res.status_code == 200:
                print(f"✅ Synced txn #{txn_id}")
            else:
                print(f"❌ Sync failed for txn #{txn_id}: {res.json()}")
        except Exception as e:
            print(f"💥 Sync error: {e}")

# -----------------------------
# 💳 Main Router Logic
# -----------------------------
def process_transaction():
    print("🧾 --- Start Transaction ---")

    # 1. Get txn input
    amount = int(input("Enter amount to send: "))
    to_user = input("Enter recipient number: ")
    sms_text = input("Paste latest SMS message: ")
    txn_time = datetime.now().strftime("%H:%M")

    txn = {
        "amount": amount,
        "to_user": to_user,
        "time": txn_time,
    }

    # 2. Phishing Detection
    phish_result = classify_sms(sms_text)
    txn["is_phishing"] = int(phish_result["is_phishing"])
    txn["flags"] = phish_result["matched_keywords"] if txn["is_phishing"] else []

    if txn["is_phishing"]:
        print("🚨 Phishing detected. Blocking transaction.")
        txn["channel"] = "Blocked"
        txn["status"] = "Blocked"
        log_transaction(txn)
        return

    # 3. Fraud Detection
    fraud_result = is_fraudulent_kmeans(txn)
    txn["is_fraud"] = int(fraud_result["is_fraud"])
    if txn["is_fraud"]:
        txn["flags"].append("KMeans Risk")

    # 4. Fallback Routing
    if check_network():
        txn["channel"] = "Online"
        txn["status"] = "Success"
        print("🌐 Sent via ONLINE")
    elif check_bluetooth():
        txn["channel"] = "Bluetooth"
        txn["status"] = "Success"
        print("📡 Sent via BLUETOOTH")
    elif check_sms():
        txn["channel"] = "SMS"
        txn["status"] = "Success"
        print("📲 Sent via SMS")
    else:
        txn["channel"] = "Ledger"
        txn["status"] = "Queued"
        print("💤 No method available. Logged locally.")

    # 5. Log Transaction
    log_transaction(txn)
    print("✅ Transaction processed & logged.")

    # 6. Sync if online
    if check_network():
        sync_unsynced_txns()

# -----------------------------
# 🔥 MAIN
# -----------------------------
if __name__ == "__main__":
    process_transaction()
