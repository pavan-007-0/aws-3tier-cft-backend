#!/usr/bin/env python3
"""
Check and fix table structures
"""
from db import get_connection

def check_and_fix_tables():
    """Check and fix table structures"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check shipping_addresses table structure
    cursor.execute("DESCRIBE shipping_addresses")
    columns = cursor.fetchall()
    
    print("📋 Current shipping_addresses table structure:")
    for col in columns:
        print(f"  {col['Field']}: {col['Type']} {'NOT NULL' if col['Null'] == 'NO' else 'NULL'}")
    
    # Check if we need to modify the table to match our new structure
    existing_columns = [col['Field'] for col in columns]
    
    # Drop and recreate the table with the correct structure
    if 'first_name' in existing_columns and 'street' in existing_columns:
        print("\n🔄 Table has mixed structure, recreating...")
        
        # Drop the table and recreate it
        cursor.execute("DROP TABLE IF EXISTS shipping_addresses")
        
        cursor.execute("""
            CREATE TABLE shipping_addresses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                order_id INT,
                street VARCHAR(255) NOT NULL,
                city VARCHAR(100) NOT NULL,
                state VARCHAR(100),
                zip_code VARCHAR(20) NOT NULL,
                country VARCHAR(100) NOT NULL,
                full_name VARCHAR(200),
                phone VARCHAR(20),
                is_default BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL
            )
        """)
        
        print("✅ Recreated shipping_addresses table with correct structure")
    
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_and_fix_tables()