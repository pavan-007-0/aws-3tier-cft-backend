#!/usr/bin/env python3
"""
Database migration script to update existing tables with new security columns
"""
from db import get_connection
import sys

def migrate_users_table():
    """Add missing columns to users table"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if phone column exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'phone'")
        if not cursor.fetchone():
            print("Adding 'phone' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20) AFTER password")
            print("✅ Added 'phone' column")
        else:
            print("✅ 'phone' column already exists")
        
        # Check if role column exists first
        cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
        if not cursor.fetchone():
            print("Adding 'role' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN role ENUM('customer', 'admin') DEFAULT 'customer' AFTER password")
            print("✅ Added 'role' column")
        else:
            # Check if role column has correct enum values
            cursor.execute("SHOW COLUMNS FROM users LIKE 'role'")
            result = cursor.fetchone()
            if result:
                column_type = result[1]  # Type column
                if 'admin' not in column_type:
                    print("Updating role column enum values...")
                    cursor.execute("ALTER TABLE users MODIFY COLUMN role ENUM('customer', 'admin') DEFAULT 'customer'")
                    print("✅ Updated role column")
                else:
                    print("✅ Role column already has correct values")
        
        # Check if is_active column exists
        cursor.execute("SHOW COLUMNS FROM users LIKE 'is_active'")
        if not cursor.fetchone():
            print("Adding 'is_active' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            print("✅ Added 'is_active' column")
        else:
            print("✅ 'is_active' column already exists")
        
        # Check if created_at and updated_at columns exist
        cursor.execute("SHOW COLUMNS FROM users LIKE 'created_at'")
        if not cursor.fetchone():
            print("Adding 'created_at' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("✅ Added 'created_at' column")
        else:
            print("✅ 'created_at' column already exists")
        
        cursor.execute("SHOW COLUMNS FROM users LIKE 'updated_at'")
        if not cursor.fetchone():
            print("Adding 'updated_at' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
            print("✅ Added 'updated_at' column")
        else:
            print("✅ 'updated_at' column already exists")
        
        conn.commit()
        print("✅ Users table migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Error migrating users table: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
    
    return True

def check_database_connection():
    """Check if database connection is working"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🔄 Starting Database Migration")
    print("=" * 50)
    
    # Check database connection
    if not check_database_connection():
        print("❌ Cannot connect to database. Please check your database configuration.")
        return 1
    
    print("✅ Database connection successful")
    
    # Run migrations
    if not migrate_users_table():
        print("❌ Migration failed!")
        return 1
    
    print("\n" + "=" * 50)
    print("🎉 Database migration completed successfully!")
    print("You can now run the tests with: python run_tests.py")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())