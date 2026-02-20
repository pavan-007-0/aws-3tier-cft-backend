from db import get_connection

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Users table with enhanced fields
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        phone VARCHAR(20),
        role ENUM('customer', 'admin') DEFAULT 'customer',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)

    # Categories table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        image VARCHAR(255),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Enhanced products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        compare_price DECIMAL(10,2),
        cost_price DECIMAL(10,2),
        sku VARCHAR(100) UNIQUE,
        barcode VARCHAR(100),
        track_quantity BOOLEAN DEFAULT TRUE,
        quantity INT DEFAULT 0,
        allow_backorder BOOLEAN DEFAULT FALSE,
        weight DECIMAL(8,2),
        category_id INT,
        brand VARCHAR(255),
        image VARCHAR(500),
        status ENUM('active', 'draft', 'archived') DEFAULT 'active',
        is_active BOOLEAN DEFAULT TRUE,
        featured BOOLEAN DEFAULT FALSE,
        seo_title VARCHAR(255),
        seo_description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
        FULLTEXT(name, description)
    )
    """)

    # Product images table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS product_images (
        id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        image_url VARCHAR(500) NOT NULL,
        alt_text VARCHAR(255),
        sort_order INT DEFAULT 0,
        is_primary BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    """)

    # Enhanced cart table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        UNIQUE KEY unique_user_product (user_id, product_id)
    )
    """)

    # Orders table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        order_number VARCHAR(50) UNIQUE NOT NULL,
        status ENUM('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded') DEFAULT 'pending',
        payment_status ENUM('pending', 'paid', 'failed', 'refunded') DEFAULT 'pending',
        payment_method VARCHAR(50),
        payment_id VARCHAR(255),
        subtotal DECIMAL(10,2) NOT NULL,
        tax_amount DECIMAL(10,2) DEFAULT 0,
        shipping_amount DECIMAL(10,2) DEFAULT 0,
        discount_amount DECIMAL(10,2) DEFAULT 0,
        total_amount DECIMAL(10,2) NOT NULL,
        currency VARCHAR(3) DEFAULT 'USD',
        notes TEXT,
        shipped_at TIMESTAMP NULL,
        delivered_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
    )
    """)

    # Order items table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        price DECIMAL(10,2) NOT NULL,
        sku VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
    )
    """)

    # Shipping addresses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipping_addresses (
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

    # Reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT NOT NULL,
        user_id INT NOT NULL,
        order_id INT,
        rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
        title VARCHAR(255),
        comment TEXT,
        is_verified BOOLEAN DEFAULT FALSE,
        is_approved BOOLEAN DEFAULT TRUE,
        helpful_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
        UNIQUE KEY unique_user_product_order (user_id, product_id, order_id)
    )
    """)

    # Wishlist table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wishlist (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        product_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        UNIQUE KEY unique_user_product (user_id, product_id)
    )
    """)

    # Coupons table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupons (
        id INT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        type ENUM('percentage', 'fixed_amount') NOT NULL,
        value DECIMAL(10,2) NOT NULL,
        minimum_amount DECIMAL(10,2) DEFAULT 0,
        maximum_discount DECIMAL(10,2),
        usage_limit INT,
        used_count INT DEFAULT 0,
        is_active BOOLEAN DEFAULT TRUE,
        starts_at TIMESTAMP,
        expires_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # Insert sample data
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO categories (name, description, image)
        VALUES (%s, %s, %s)
        """, [
            ("Electronics", "Latest gadgets and electronic devices", "electronics.jpg"),
            ("Accessories", "Tech accessories and peripherals", "accessories.jpg"),
            ("Wearables", "Smart watches and fitness trackers", "wearables.jpg"),
        ])
        conn.commit()

    # Insert sample products with enhanced data
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO products (name, description, price, compare_price, sku, quantity, category_id, brand, image, featured)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            ("Bluetooth Earbuds", "Waterproof, Touch controls, Active Noise Cancellation", 1299.00, 1428.00, "BT-EARBUDS-01", 50, 1, "AudioTech", "earbuds.jpg", True),
            ("Gaming Mouse", "RGB lighting, 6 programmable buttons, 16000 DPI", 899.00, 998.00, "GM-MOUSE-01", 40, 2, "GameGear", "mouse.jpg", True),
            ("Laptop Stand", "Aluminum, Adjustable height, Ergonomic design", 849.00, 933.00, "LP-STAND-01", 30, 2, "ErgoDesk", "laptopstand.jpg", True),
            ("Meta Glasses", "AR Smart Glasses, Immersive VR experience", 5999.00, 6598.00, "META-GL-01", 15, 1, "Meta", "glasses.jpg", True),
            ("Portable Speaker", "360° sound, Waterproof, 12hr battery", 599.00, 699.00, "PT-SPKR-01", 45, 1, "SoundWave", "speaker.jpg", False),
            ("Power Bank", "20000mAh, Fast charging, USB-C", 499.00, 599.00, "PW-BANK-01", 60, 2, "PowerMax", "powerbank.jpg", False),
            ("Smart Mobile", "iPhone Pro, Triple camera, A17 Pro chip", 1199.00, 1399.00, "SM-MOB-01", 25, 1, "Apple", "mobile.jpg", True),
            ("Smart Watch", "GPS + Cellular, Health monitoring, AMOLED display", 429.00, 499.00, "SM-WATCH-01", 35, 3, "WearTech", "smartwatch.jpg", True),
            ("Webcam HD Pro", "4K Ultra HD, Auto-focus, Streaming ready", 349.00, 399.00, "WC-PRO-01", 30, 1, "StreamCam", "webcam.jpg", False),
            ("Headphones Pro", "Studio-grade, Over-ear, 40hr battery", 799.00, 899.00, "HP-PRO-01", 20, 1, "SoundMaster", "headphones.jpg", True),
        ])
        conn.commit()

    # Insert sample product images
    cursor.execute("SELECT COUNT(*) FROM product_images")
    if cursor.fetchone()[0] == 0:
        # Get the first 5 product IDs
        cursor.execute("SELECT id FROM products ORDER BY id LIMIT 5")
        product_ids = [row[0] for row in cursor.fetchall()]
        
        if len(product_ids) >= 5:
            cursor.executemany("""
            INSERT INTO product_images (product_id, image_url, alt_text, is_primary)
            VALUES (%s, %s, %s, %s)
            """, [
                (product_ids[0], "wireless-headphones.jpg", "Wireless Headphones", True),
                (product_ids[1], "smart-watch.jpg", "Smart Watch", True),
                (product_ids[2], "gaming-mouse.jpg", "Gaming Mouse", True),
                (product_ids[3], "smart-mobile.jpg", "Smart Mobile", True),
                (product_ids[4], "portable-speaker.jpg", "Portable Speaker", True),
            ])
            conn.commit()

    cursor.close()
    conn.close()
    print("✅ Enhanced database tables created successfully!")
    conn.close()
    print("✔ Tables checked/created and sample products inserted if needed.")
