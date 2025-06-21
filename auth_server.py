import sqlite3
import bcrypt
import os

BASE_DIR = r"D:\The New Data Trio"
DB_PATH = os.path.join(BASE_DIR, "ledger.db")

# Store the logged-in user in-memory (you can move this to a better place later)
current_user = {"username": None}


def init_user_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ User table initialized.")


def signup_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check for duplicate
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        print("❌ Username already exists. Choose another.")
        return False

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_pw))
    conn.commit()
    conn.close()

    # Set the current user
    current_user["username"] = username
    print(f"✅ User '{username}' signed up and logged in.")
    return True


def login_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT password_hash FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row and bcrypt.checkpw(password.encode(), row[0]):
        current_user["username"] = username
        print(f"✅ Logged in as {username}")
        return True
    else:
        print("❌ Login failed: Invalid username or password.")
        return False


def get_current_user():
    return current_user.get("username")
