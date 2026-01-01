#!/usr/bin/env python3
"""
Fix missing quantity column in products table
"""
from db import get_connection

def fix_quantity():
    """Add quantity column to products table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Add quantity column
        cursor.execute("ALTER TABLE products ADD COLUMN quantity INT DEFAULT 0")
        print("✅ Added quantity column to products table")
    except Exception as e:
        if "Duplicate column name" in str(e):
            print("✅ quantity column already exists in products table")
        else:
            print(f"❌ Error adding quantity: {e}")
    
    try:
        # Update products with stock quantities
        cursor.execute("""
            UPDATE products SET quantity = CASE 
                WHEN name LIKE '%MacBook%' THEN 25
                WHEN name LIKE '%AirPods%' THEN 50
                WHEN name LIKE '%Apple Watch%' THEN 30
                WHEN name LIKE '%iPad%' THEN 40
                WHEN name LIKE '%Magic Keyboard%' THEN 20
                ELSE 10
            END
            WHERE quantity = 0 OR quantity IS NULL
        """)
        
        conn.commit()
        print("✅ Updated product quantities")
        
    except Exception as e:
        print(f"❌ Error updating quantities: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_quantity()