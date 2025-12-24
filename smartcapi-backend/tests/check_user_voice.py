import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3

# Connect to the database
conn = sqlite3.connect('smartcapi.db')
cursor = conn.cursor()

# Query all users and their voice sample paths
cursor.execute("SELECT id, username, voice_sample_path FROM users")
users = cursor.fetchall()

print("User ID | Username | Voice Sample Path")
print("-" * 60)
for user in users:
    print(f"{user[0]:7} | {user[1]:20} | {user[2]}")

conn.close()
