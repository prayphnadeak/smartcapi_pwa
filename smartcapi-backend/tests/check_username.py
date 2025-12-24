import sqlite3
import sys
import io
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('smartcapi.db')
cursor = conn.cursor()

username = "pray25"
print(f"Checking for username '{username}'...")
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
user = cursor.fetchone()

if user:
    print(f"✅ User '{username}' FOUND:")
    print(user)
else:
    print(f"❌ User '{username}' NOT FOUND in database!")

# Also list all users just in case
print("\nAll users:")
cursor.execute("SELECT id, username FROM users")
for row in cursor.fetchall():
    print(row)

conn.close()
