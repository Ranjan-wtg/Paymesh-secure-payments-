# ledger.py (Fixed for auto-creation and phone number storage)

import sqlite3
import os
import bcrypt
import time
from datetime import datetime

# 📁 Auto-create base directory if it doesn't exist
BASE_DIR = r"D:\The New Data Trio"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)
    print(f"✅ Created directory: {BASE_DIR}")

DB_PATH = os.path.join(BASE_DIR, "ledger.db")

# Global session management
current_user_session = {}

# ====== DATABASE INITIALIZATION ======

def ensure_database_exists():
    """Ensure database and all tables exist - called before any operation"""
    if not os.path.exists(DB_PATH):
        print("📝 Database not found. Creating new database...")
        initialize_all_tables()
    else:
        # Ensure all tables exist even if DB file exists
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            # Check if users table has all required columns
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'phone_number' not in columns:
                print("📝 Updating database schema...")
                cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
                cursor.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
                cursor.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
                conn.commit()
                print("✅ Database schema updated")
            
            conn.close()
        except Exception as e:
            print(f"⚠️ Database check error: {e}")
            initialize_all_tables()

def initialize_all_tables():
    """Initialize all database tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users table with proper phone number as TEXT
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone_number TEXT,
            created_at TEXT,
            last_login TEXT
        )
    ''')
    
    # Login attempts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            username TEXT PRIMARY KEY,
            attempts INTEGER DEFAULT 0,
            last_attempt REAL
        )
    ''')
    
    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT,
            recipient TEXT,
            amount REAL,
            time TEXT,
            channel TEXT,
            is_fraud INTEGER,
            is_phishing INTEGER,
            status TEXT,
            flags TEXT,
            synced INTEGER DEFAULT 0,
            txn_id TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ All database tables initialized successfully!")

# ====== PASSWORD FUNCTIONS ======

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ====== USER MANAGEMENT ======

def create_user(username, password, phone_number=""):
    """Create user with automatic database creation"""
    # Ensure database exists first
    ensure_database_exists()
    
    # Input validation
    if not username or not password:
        return {"success": False, "message": "Username and password are required"}
    
    if len(username) < 3:
        return {"success": False, "message": "Username must be at least 3 characters"}
    
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters"}
    
    # Ensure phone number is stored as string (not scientific notation)
    if phone_number and phone_number.isdigit():
        phone_number = str(phone_number)  # Keep as string
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, phone_number, created_at) 
            VALUES (?, ?, ?, ?)
        ''', (username, hashed_pw, phone_number, created_at))
        
        conn.commit()
        user_id = cursor.lastrowid
        print(f"✅ User '{username}' created successfully with ID {user_id}")
        
        return {
            "success": True, 
            "message": f"User {username} created successfully",
            "user_id": user_id
        }
        
    except sqlite3.IntegrityError:
        print(f"⚠️ Username '{username}' already exists")
        return {"success": False, "message": "Username already exists"}
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return {"success": False, "message": f"Registration failed: {str(e)}"}
    finally:
        conn.close()

def verify_user(username, password):
    """Verify user login with automatic database creation"""
    # Ensure database exists first
    ensure_database_exists()
    
    if not username or not password:
        return {"success": False, "message": "Username and password are required"}
    
    # Check brute force protection
    if is_locked_out(username):
        remaining_time = get_lockout_remaining_time(username)
        return {
            "success": False, 
            "message": "Account temporarily locked",
            "locked": True,
            "wait_time": remaining_time
        }
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, password_hash, phone_number, last_login 
        FROM users WHERE username=?
    ''', (username,))
    row = cursor.fetchone()

    if not row:
        record_login_attempt(username, False)
        conn.close()
        return {"success": False, "message": "User not found"}

    user_id, db_username, hashed, phone_number, last_login = row
    
    if verify_password(password, hashed):
        # Successful login
        record_login_attempt(username, True)
        
        # Update last login time
        now = datetime.now().isoformat()
        cursor.execute("UPDATE users SET last_login=? WHERE username=?", (now, username))
        conn.commit()
        conn.close()
        
        # Set current user session with properly formatted phone
        user_data = {
            "user_id": user_id,
            "username": db_username,
            "phone_number": format_phone_number(phone_number),
            "last_login": last_login,
            "current_login": now
        }
        set_current_user(user_data)
        
        print(f"✅ User '{username}' logged in successfully")
        return {
            "success": True, 
            "message": f"Welcome back, {username}!",
            "user_data": user_data
        }
    else:
        # Failed login
        record_login_attempt(username, False)
        conn.close()
        
        remaining = get_remaining_attempts(username)
        if remaining <= 0:
            return {
                "success": False, 
                "message": "Invalid password. Account locked due to too many attempts.",
                "locked": True,
                "wait_time": 60
            }
        else:
            return {
                "success": False, 
                "message": f"Invalid password. {remaining} attempts remaining."
            }

def format_phone_number(phone_str):
    """Fix phone number from scientific notation to normal format"""
    if not phone_str:
        return ""
    
    try:
        # If it's in scientific notation, convert it back
        if 'e+' in str(phone_str):
            return str(int(float(phone_str)))
        return str(phone_str)
    except (ValueError, TypeError):
        return str(phone_str) if phone_str else ""

# ====== SESSION MANAGEMENT ======

def get_current_user():
    """Get the currently logged in user"""
    return current_user_session if current_user_session else None

def set_current_user(user_data):
    """Set the current user session"""
    global current_user_session
    current_user_session = user_data

def clear_current_user():
    """Clear the current user session"""
    global current_user_session
    current_user_session = {}

# ====== BRUTE FORCE PROTECTION ======

MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 60

def is_locked_out(username):
    ensure_database_exists()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT attempts, last_attempt FROM login_attempts WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return False

    attempts, last_time = row
    if attempts < MAX_ATTEMPTS:
        return False

    if time.time() - last_time > LOCKOUT_SECONDS:
        reset_attempts(username)
        return False

    return True

def get_lockout_remaining_time(username):
    ensure_database_exists()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT last_attempt FROM login_attempts WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return 0
    
    last_time = row[0]
    elapsed = time.time() - last_time
    remaining = max(0, LOCKOUT_SECONDS - elapsed)
    return int(remaining)

def get_remaining_attempts(username):
    ensure_database_exists()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT attempts FROM login_attempts WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return MAX_ATTEMPTS
    
    attempts = row[0]
    return max(0, MAX_ATTEMPTS - attempts)

def record_login_attempt(username, success):
    ensure_database_exists()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = time.time()

    if success:
        cursor.execute("DELETE FROM login_attempts WHERE username=?", (username,))
    else:
        cursor.execute("INSERT OR IGNORE INTO login_attempts (username, attempts, last_attempt) VALUES (?, 0, ?)", (username, now))
        cursor.execute("UPDATE login_attempts SET attempts = attempts + 1, last_attempt=? WHERE username=?", (now, username))

    conn.commit()
    conn.close()

def reset_attempts(username):
    ensure_database_exists()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM login_attempts WHERE username=?", (username,))
    conn.commit()
    conn.close()

# ====== TRANSACTION LOGGING ======

def log_transaction(sender, recipient, amount, channel="manual", is_fraud=False, is_phishing=False, txn_id=None, status="completed"):
    """Log transaction to database"""
    ensure_database_exists()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not txn_id:
        txn_id = f"TXN_{int(time.time())}"
    
    time_str = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO transactions (sender, recipient, amount, time, channel,
            is_fraud, is_phishing, status, txn_id, synced)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (
        sender, recipient, amount, time_str, channel,
        int(is_fraud), int(is_phishing), status, txn_id
    ))

    conn.commit()
    conn.close()
    print(f"📝 Transaction logged: {txn_id}")
    return txn_id

def get_transaction_count(username):
    """Get total transaction count for a user"""
    ensure_database_exists()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM transactions 
        WHERE sender=? OR recipient=?
    ''', (username, username))
    count = cursor.fetchone()[0]
    conn.close()
    return count

# ====== UTILITY FUNCTIONS ======

def get_all_users():
    """Get all users for debugging"""
    ensure_database_exists()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, phone_number, created_at, last_login FROM users")
    rows = cursor.fetchall()
    conn.close()
    return rows

# ====== INITIALIZATION ON MODULE LOAD ======

# Automatically ensure database exists when module is imported
try:
    ensure_database_exists()
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# ====== TEST FUNCTIONS ======

if __name__ == "__main__":
    print("🚀 PayMesh Database System")
    print(f"📂 Database location: {DB_PATH}")
    
    # Show existing users
    users = get_all_users()
    if users:
        print("\n👥 Existing users:")
        for user in users:
            phone = format_phone_number(user[2])
            print(f"  • {user[1]} (Phone: {phone})")
    else:
        print("\n👥 No users found")
    
    # Option to create test user
    choice = input("\n🔧 Create a test user? (y/n): ").strip().lower()
    if choice == 'y':
        username = input("Username: ")
        password = input("Password: ")
        phone = input("Phone (optional): ")
        
        result = create_user(username, password, phone)
        print(f"\nResult: {result}")
        
        if result["success"]:
            test_login = input("\n🧪 Test login? (y/n): ").strip().lower()
            if test_login == 'y':
                login_result = verify_user(username, password)
                print(f"Login result: {login_result}")
                
                if login_result["success"]:
                    current = get_current_user()
                    print(f"Current user session: {current}")
