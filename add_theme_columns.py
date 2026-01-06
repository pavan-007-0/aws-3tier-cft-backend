#!/usr/bin/env python3
"""
Add theme preference columns to users table
"""
from db import get_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_theme_columns():
    """Add theme preference columns to users table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'users' 
            AND COLUMN_NAME IN ('theme_id', 'theme_name', 'is_dark_mode')
        """)
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        # Add theme_id column if it doesn't exist
        if 'theme_id' not in existing_columns:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN theme_id VARCHAR(50) DEFAULT 'light-blue'
            """)
            logger.info("Added theme_id column")
        
        # Add theme_name column if it doesn't exist
        if 'theme_name' not in existing_columns:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN theme_name VARCHAR(50) DEFAULT 'light-blue'
            """)
            logger.info("Added theme_name column")
        
        # Add is_dark_mode column if it doesn't exist
        if 'is_dark_mode' not in existing_columns:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN is_dark_mode BOOLEAN DEFAULT FALSE
            """)
            logger.info("Added is_dark_mode column")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ Theme columns added successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error adding theme columns: {e}")
        raise

if __name__ == "__main__":
    add_theme_columns()