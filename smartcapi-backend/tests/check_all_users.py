import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3

# Connect to the database
conn = sqlite3.connect('smartcapi.db')
cursor = conn.cursor()

# Query all users
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()

# Get column names
column_names = [description[0] for description in cursor.description]

print("All users in database:")
print("-" * 100)
for user in users:
    print("\nUser:")
    for i, name in enumerate(column_names):
        print(f"  {name}: {user[i]}")

conn.close()
