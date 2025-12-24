import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3

# Connect to the database
conn = sqlite3.connect('smartcapi.db')
cursor = conn.cursor()

# Count users
cursor.execute("SELECT COUNT(*) FROM users")
count = cursor.fetchone()[0]
print(f"Total users: {count}")

# Get all usernames and IDs
cursor.execute("SELECT id, username, email, voice_sample_path FROM users ORDER BY id")
users = cursor.fetchall()

print("\nAll users:")
for user in users:
    print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Voice path: {user[3]}")

# Check table schema
cursor.execute("PRAGMA table_info(users)")
schema = cursor.fetchall()

print("\nUsers table schema:")
for col in schema:
    print(f"  {col[1]} ({col[2]})")

conn.close()
