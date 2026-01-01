#!/usr/bin/env python3
"""
Check what products exist in the database
"""
from db import get_connection

def check_products():
    """Check products in database"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT id, name, price, quantity, is_active FROM products LIMIT 10")
    products = cursor.fetchall()
    
    print("📦 Products in database:")
    for product in products:
        print(f"  ID: {product['id']}, Name: {product['name']}, Price: ${product['price']}, Stock: {product['quantity']}, Active: {product['is_active']}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_products()