#!/usr/bin/env python3
"""
Check order_items table structure
"""
from db import get_connection

def check_order_items():
    """Check order_items table structure"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("DESCRIBE order_items")
    columns = cursor.fetchall()
    
    print("📋 Current order_items table structure:")
    for col in columns:
        print(f"  {col['Field']}: {col['Type']} {'NOT NULL' if col['Null'] == 'NO' else 'NULL'}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_order_items()