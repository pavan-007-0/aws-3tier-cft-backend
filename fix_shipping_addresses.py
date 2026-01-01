#!/usr/bin/env python3
"""
Fix shipping addresses table structure
"""
from db import get_connection

def fix_shipping_addresses():
    """Update shipping addresses table structure"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Add missing columns to shipping_addresses table
        columns_to_add = [
            ("street", "VARCHAR(255)"),
            ("zip_code", "VARCHAR(20)"),
            ("full_name", "VARCHAR(200)")
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE shipping_addresses ADD COLUMN {column_name} {column_def}")
                print(f"✅ Added {column_name} column to shipping_addresses table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"✅ {column_name} column already exists in shipping_addresses table")
                else:
                    print(f"❌ Error adding {column_name} to shipping_addresses: {e}")
        
        conn.commit()
        print("✅ Shipping addresses table updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating shipping_addresses: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_shipping_addresses()