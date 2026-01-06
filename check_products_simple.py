from db import get_connection

def check_products():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT name, brand, price, quantity FROM products WHERE status = "active" LIMIT 10')
        products = cursor.fetchall()
        
        print('Products in database:')
        for p in products:
            brand_info = f" by {p['brand']}" if p.get('brand') else ""
            print(f'- {p["name"]}{brand_info} - ${p["price"]} (Stock: {p["quantity"]})')
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_products()