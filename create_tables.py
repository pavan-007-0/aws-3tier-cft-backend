from db import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        email VARCHAR(255) UNIQUE,
        password VARCHAR(255)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255),
        price INT,
        image VARCHAR(255),
        description TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        product_id INT,
        quantity INT
    )
    """)

    conn.commit()

    # Insert sample products only if products table empty
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO products (name, price, image, description)
        VALUES (%s, %s, %s, %s)
        """, [
            ("Laptop Stand", 849, "laptop-stand.jpg", "Adjustable aluminum laptop stand"),
            ("Smart Watch", 3499, "smartwatch.jpg", "Waterproof smartwatch with heart-rate sensor"),
            ("Wireless Headphones", 1999, "wireless-headphones.jpg", "Bluetooth 5.2, noise cancelling"),
        ])
        conn.commit()

    cursor.close()
    conn.close()
    print("✔ Tables checked/created and sample products inserted if needed.")
