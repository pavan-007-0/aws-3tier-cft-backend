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
        
        # Update sample products with enhanced data - FIXED to assign correct images
        cursor.execute("""
            UPDATE products SET 
                image = CASE 
                    WHEN name LIKE '%Wireless Earbuds%' OR name LIKE '%Earbuds%' THEN '/assets/products/earbuds.jpg'
                    WHEN name LIKE '%Smart Glasses%' OR name LIKE '%Glasses%' THEN '/assets/products/glasses.jpg'
                    WHEN name LIKE '%Headphones%' THEN '/assets/products/headphones.jpg'
                    WHEN name LIKE '%Laptop%' OR name LIKE '%Stand%' THEN '/assets/products/laptopstand.jpg'
                    WHEN name LIKE '%Mobile%' OR name LIKE '%Phone%' OR name LIKE '%Smartphone%' THEN '/assets/products/mobile.jpg'
                    WHEN name LIKE '%Mouse%' THEN '/assets/products/mouse.jpg'
                    WHEN name LIKE '%Power%' OR name LIKE '%Bank%' THEN '/assets/products/powerbank.jpg'
                    WHEN name LIKE '%Smart Watch%' OR name LIKE '%Watch%' THEN '/assets/products/smartwatch.jpg'
                    WHEN name LIKE '%Speaker%' THEN '/assets/products/speaker.jpg'
                    WHEN name LIKE '%Webcam%' OR name LIKE '%Camera%' THEN '/assets/products/webcam.jpg'
                    ELSE '/assets/products/placeholder.jpg'
                END,
                compare_price = CASE 
                    WHEN compare_price IS NULL OR compare_price <= price THEN price * 1.15
                    ELSE compare_price
                END,
                sku = CASE 
                    WHEN sku IS NULL OR sku = '' THEN CONCAT('SKU-', id, '-', UPPER(SUBSTRING(name, 1, 3)))
                    ELSE sku
                END,
                category_id = CASE 
                    WHEN category_id IS NULL THEN 1
                    ELSE category_id
                END,
                featured = CASE 
                    WHEN featured IS NULL THEN FALSE
                    ELSE featured
                END,
                is_active = TRUE
            WHERE TRUE
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