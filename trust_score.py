import sqlite3
import os
import numpy as np

BASE_DIR = r"D:\The New Data Trio"
DB_PATH = os.path.join(BASE_DIR, "ledger.db")

# 🚦 Main function
def get_trust_score(txn, history_limit=30):
    """
    txn = {
        "amount": 17000,
        "time": "00:30"
    }
    """

    # 1. Fetch recent legit txns
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT amount, time FROM transactions
        WHERE is_fraud=0 AND status='Success'
        ORDER BY id DESC
        LIMIT ?
    ''', (history_limit,))
    rows = cursor.fetchall()
    conn.close()

    if len(rows) < 5:
        return {"trust_score": 0.5, "risk_factors": ["not_enough_history"]}

    amounts = np.array([row[0] for row in rows], dtype=np.float32)
    times = []

    for row in rows:
        try:
            h, m = map(int, row[1].split(":"))
            times.append(h + m / 60.0)
        except:
            continue

    # 2. Current txn info
    try:
        amt = txn["amount"]
        hour = int(txn["time"].split(":")[0]) + int(txn["time"].split(":")[1]) / 60
    except:
        return {"trust_score": 0.0, "risk_factors": ["invalid_time"]}

    # 3. Analyze risks
    risk_factors = []

    # 🚩 Amount outlier
    amt_mean = np.mean(amounts)
    amt_std = np.std(amounts)
    if abs(amt - amt_mean) > 2 * amt_std:
        risk_factors.append("amount_outlier")

    # 🚩 Odd time
    if not (7 <= hour <= 22):
        risk_factors.append("odd_hour")

    # 4. Final trust score (1 - penalty for each factor)
    base_score = 1.0
    penalty = 0.25 * len(risk_factors)
    score = max(0.0, base_score - penalty)

    return {
        "trust_score": round(score, 2),
        "risk_factors": risk_factors
    }

# ✅ Test block
if __name__ == "__main__":
    txn = {"amount": 18000, "time": "01:15"}
    result = get_trust_score(txn)
    print("🧠 Trust Score:")
    print(result)
