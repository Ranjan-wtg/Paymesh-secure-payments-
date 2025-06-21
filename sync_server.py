from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)
BASE_DIR = r"D:\The New Data Trio"
DB_PATH = os.path.join(BASE_DIR, "ledger.db")

@app.route("/")
def home():
    return "🟢 Sync server is running", 200

@app.route("/sync", methods=["POST"])
def sync_transaction():
    data = request.get_json()
    txn_id = data.get("id")

    if not txn_id:
        return jsonify({"status": "error", "msg": "Missing txn_id"}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE transactions SET synced=1 WHERE id=?", (txn_id,))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "msg": f"Txn {txn_id} synced"}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route("/upload", methods=["POST"])
def upload_transaction():
    data = request.get_json()
    print("✅ Received txn via /upload:", data)
    return jsonify({"status": "success", "msg": "Transaction received"}), 200

@app.route("/unsynced", methods=["GET"])
def get_unsynced():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions WHERE synced=0")
        rows = cursor.fetchall()
        conn.close()
        return jsonify({"status": "success", "txns": rows}), 200
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
