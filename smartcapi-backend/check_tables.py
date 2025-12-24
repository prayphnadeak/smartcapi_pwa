import sqlite3
try:
    con = sqlite3.connect('smartcapi.db')
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:")
    for t in tables:
        print(f"- {t[0]}")
    
    # Check specifically for role_event_logs
    has_role = any(t[0] == 'role_event_logs' for t in tables)
    print(f"\nrole_event_logs exists: {has_role}")
    
except Exception as e:
    print(f"Error: {e}")
