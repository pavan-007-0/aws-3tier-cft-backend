#!/usr/bin/env python3
"""
Update database schema for enhanced e-commerce features
"""
from db import get_connection

def update_schema():
    """Update database schema with missing columns and indexes"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("🔄 Updating database schema...")
    
    try:
        # Add missing columns to cart table
        try:
            cursor.execute("ALTER TABLE cart ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
            print("✅ Added updated_at column to cart table")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✅ updated_at column already exists in cart table")
            else:
                print(f"❌ Error adding updated_at to cart: {e}")
        
        # Add missing columns to products table
        columns_to_add = [
            ("image", "VARCHAR(500)"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("compare_price", "DECIMAL(10,2)"),
            ("cost_price", "DECIMAL(10,2)"),
            ("sku", "VARCHAR(100)"),
            ("barcode", "VARCHAR(100)"),
            ("track_quantity", "BOOLEAN DEFAULT TRUE"),
            ("allow_backorder", "BOOLEAN DEFAULT FALSE"),
            ("weight", "DECIMAL(8,2)"),
            ("category_id", "INT"),
            ("brand", "VARCHAR(255)"),
            ("status", "ENUM('active', 'draft', 'archived') DEFAULT 'active'"),
            ("featured", "BOOLEAN DEFAULT FALSE"),
            ("seo_title", "VARCHAR(255)"),
            ("seo_description", "TEXT"),
            ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE products ADD COLUMN {column_name} {column_def}")
                print(f"✅ Added {column_name} column to products table")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"✅ {column_name} column already exists in products table")
                else:
                    print(f"❌ Error adding {column_name} to products: {e}")
        
        # Update existing products to have is_active = TRUE if NULL
        cursor.execute("UPDATE products SET is_active = TRUE WHERE is_active IS NULL")
        
        # Add FULLTEXT index for search
        try:
            cursor.execute("ALTER TABLE products ADD FULLTEXT(name, description)")
            print("✅ Added FULLTEXT index to products table")
        except Exception as e:
            if "Duplicate key name" in str(e) or "already exists" in str(e):
                print("✅ FULLTEXT index already exists on products table")
            else:
                print(f"❌ Error adding FULLTEXT index: {e}")
        
        # Update sample products with enhanced data
        cursor.execute("""
            UPDATE products SET 
                image = CASE 
                    WHEN name LIKE '%MacBook%' THEN 'macbook-pro-14.jpg'
                    WHEN name LIKE '%AirPods%' THEN 'airpods-pro-3.jpg'
                    WHEN name LIKE '%Apple Watch%' THEN 'apple-watch-s9.jpg'
                    WHEN name LIKE '%iPad%' THEN 'ipad-air-11.jpg'
                    WHEN name LIKE '%Magic Keyboard%' THEN 'magic-keyboard.jpg'
                    ELSE 'default-product.jpg'
                END,
                compare_price = CASE 
                    WHEN name LIKE '%MacBook%' THEN 2199.00
                    WHEN name LIKE '%AirPods%' THEN 279.00
                    WHEN name LIKE '%Apple Watch%' THEN 459.00
                    WHEN name LIKE '%iPad%' THEN 649.00
                    WHEN name LIKE '%Magic Keyboard%' THEN 329.00
                    ELSE price * 1.1
                END,
                sku = CASE 
                    WHEN name LIKE '%MacBook%' THEN 'MBP-14-M3-16-512'
                    WHEN name LIKE '%AirPods%' THEN 'APP-3GEN'
                    WHEN name LIKE '%Apple Watch%' THEN 'AWS9-45-MID'
                    WHEN name LIKE '%iPad%' THEN 'IPAD-AIR-11-M2'
                    WHEN name LIKE '%Magic Keyboard%' THEN 'MK-IPAD-11'
                    ELSE CONCAT('SKU-', id)
                END,
                brand = 'Apple',
                category_id = CASE 
                    WHEN name LIKE '%MacBook%' OR name LIKE '%iPad%' THEN 1
                    WHEN name LIKE '%AirPods%' OR name LIKE '%Magic Keyboard%' THEN 2
                    WHEN name LIKE '%Apple Watch%' THEN 3
                    ELSE 1
                END,
                featured = CASE 
                    WHEN name LIKE '%MacBook%' OR name LIKE '%AirPods%' OR name LIKE '%Apple Watch%' THEN TRUE
                    ELSE FALSE
                END
            WHERE image IS NULL OR compare_price IS NULL OR sku IS NULL
        """)
        
        conn.commit()
        print("✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_schema()