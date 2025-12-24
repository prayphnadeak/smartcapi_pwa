"""
Check all users in the database
"""
import sqlite3
import sys
import io
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Connect to the database in parent directory
conn = sqlite3.connect('smartcapi.db')
cursor = conn.cursor()

# Query all users
cursor.execute("SELECT id, username, email, full_name, role, voice_sample_path FROM users ORDER BY id")
users = cursor.fetchall()

print("=" * 80)
print("  DAFTAR SEMUA USER DI DATABASE")
print("=" * 80)

if not users:
    print("❌ Tidak ada user dalam database!")
else:
    print(f"\n📊 Total user: {len(users)}\n")
    for user in users:
        print(f"ID: {user[0]}")
        print(f"   Username: {user[1]}")
        print(f"   Email: {user[2]}")
        print(f"   Full Name: {user[3] or '(tidak ada)'}")
        print(f"   Role: {user[4]}")
        print(f"   Voice Sample: {user[5] or '(tidak ada)'}")
        print("-" * 80)

conn.close()
