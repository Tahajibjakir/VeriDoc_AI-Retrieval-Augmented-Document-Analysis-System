import sqlite3
import os

db_path = "sql_app.db"

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("Adding job_title column...")
        cursor.execute("ALTER TABLE user ADD COLUMN job_title VARCHAR")
    except sqlite3.OperationalError as e:
        print(f"Skipping job_title: {e}")
        
    try:
        print("Adding organization column...")
        cursor.execute("ALTER TABLE user ADD COLUMN organization VARCHAR")
    except sqlite3.OperationalError as e:
        print(f"Skipping organization: {e}")
        
    try:
        print("Adding industry column...")
        cursor.execute("ALTER TABLE user ADD COLUMN industry VARCHAR")
    except sqlite3.OperationalError as e:
        print(f"Skipping industry: {e}")
        
    conn.commit()
    conn.close()
    print("Database migration successful.")
else:
    print(f"Database not found at {db_path}")
