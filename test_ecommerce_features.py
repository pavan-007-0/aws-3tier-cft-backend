#!/usr/bin/env python3
"""
Simple test script for enhanced e-commerce features
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

def test_products_api():
    """Test enhanced products API"""
    print("🛍️  Testing Products API...")
    
    # Test get all products
    response = requests.get(f"{BASE_URL}/products")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Products fetched: {len(data.get('products', []))} items")
        print(f"   Pagination: {data.get('pagination', {})}")
    else:
        print(f"❌ Failed to fetch products: {response.status_code}")
    
    # Test product search
    response = requests.get(f"{BASE_URL}/products/search?q=MacBook")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search results: {len(data.get('products', []))} items for 'MacBook'")
    else:
        print(f"❌ Search failed: {response.status_code}")
    
    # Test categories
    response = requests.get(f"{BASE_URL}/products/categories")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Categories fetched: {len(data.get('categories', []))} categories")
    else:
        print(f"❌ Failed to fetch categories: {response.status_code}")

def test_auth_flow():
    """Test authentication flow"""
    print("\n🔐 Testing Authentication...")
    
    # Test registration
    user_data = {
        "name": "Test User",
        "email": f"testuser_{int(time.time())}@example.com",
        "password": "SecurePass123!",
        "phone": "+1234567890"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    if response.status_code == 201:
        print("✅ User registration successful")
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None
    
    # Test login
    login_data = {
        "email": user_data["email"],
        "password": user_data["password"]
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful")
        return data.get("access_token")
    else:
        print(f"❌ Login failed: {response.status_code} - {response.text}")
        return None

def test_cart_operations(token):
    """Test cart operations"""
    if not token:
        print("❌ No token available for cart tests")
        return
    
    print("\n🛒 Testing Cart Operations...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add item to cart
    cart_data = {"product_id": 17, "quantity": 2}  # Use existing product ID
    response = requests.post(f"{BASE_URL}/cart/add", json=cart_data, headers=headers)
    if response.status_code == 201:
        print("✅ Item added to cart")
    else:
        print(f"❌ Failed to add to cart: {response.status_code} - {response.text}")
    
    # Get cart
    response = requests.get(f"{BASE_URL}/cart", headers=headers)
    if response.status_code == 200:
        data = response.json()
        cart_items = data.get('cart', {}).get('items', [])
        print(f"✅ Cart fetched: {len(cart_items)} items")
        return len(cart_items) > 0
    else:
        print(f"❌ Failed to fetch cart: {response.status_code}")
        return False

def test_order_creation(token):
    """Test order creation"""
    if not token:
        print("❌ No token available for order tests")
        return
    
    print("\n📦 Testing Order Creation...")
    headers = {"Authorization": f"Bearer {token}"}
    
    order_data = {
        "shipping_address": {
            "street": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "zip_code": "12345",
            "country": "USA",
            "full_name": "Test User",
            "phone": "+1234567890"
        },
        "payment_method": "card",
        "notes": "Test order"
    }
    
    response = requests.post(f"{BASE_URL}/orders", json=order_data, headers=headers)
    if response.status_code == 201:
        data = response.json()
        print(f"✅ Order created: {data.get('order', {}).get('order_number')}")
    else:
        print(f"❌ Failed to create order: {response.status_code} - {response.text}")

def main():
    """Run all tests"""
    print("🚀 Starting E-commerce Feature Tests")
    print("=" * 50)
    
    # Test products (no auth required)
    test_products_api()
    
    # Test auth flow and get token
    token = test_auth_flow()
    
    # Test cart operations
    has_cart_items = test_cart_operations(token)
    
    # Test order creation (only if cart has items)
    if has_cart_items:
        test_order_creation(token)
    else:
        print("\n📦 Skipping order creation (no items in cart)")
    
    print("\n" + "=" * 50)
    print("🎉 E-commerce feature tests completed!")

if __name__ == "__main__":
    main()