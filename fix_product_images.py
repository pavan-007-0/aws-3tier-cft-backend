#!/usr/bin/env python3
"""
One-time script to fix product image filenames in the database.
Maps product names to the correct image files that exist in:
  frontend-app/src/assets/products/

Run this once: python fix_product_images.py
"""
from dotenv import load_dotenv
load_dotenv()

from db import get_connection

# Map keywords in product names -> correct image filename
IMAGE_RULES = [
    (["earbuds", "earbud", "airpods", "buds", "bluetooth earbuds"],  "earbuds.jpg"),
    (["glasses", "glass", "meta", "ar smart", "vr", "quest"],        "glasses.jpg"),
    (["headphones", "headphone", "headset", "over-ear"],              "headphones.jpg"),
    (["laptop", "stand", "macbook", "ipad", "keyboard"],              "laptopstand.jpg"),
    (["mobile", "phone", "smartphone", "iphone"],                     "mobile.jpg"),
    (["mouse", "gaming mouse"],                                       "mouse.jpg"),
    (["power", "powerbank", "bank", "charger"],                       "powerbank.jpg"),
    (["watch", "smartwatch", "wearable"],                             "smartwatch.jpg"),
    (["speaker", "bluetooth speaker", "portable speaker"],            "speaker.jpg"),
    (["webcam", "camera", "cam", "streaming"],                        "webcam.jpg"),
]

def resolve_image(product_name: str) -> str:
    """Given a product name, return the best matching image filename."""
    name_lower = product_name.lower()
    for keywords, image_file in IMAGE_RULES:
        if any(kw in name_lower for kw in keywords):
            return image_file
    return "default-product.jpg"

def fix_images():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, image FROM products")
    products = cursor.fetchall()

    print(f"Found {len(products)} products. Fixing images...\n")

    updated = 0
    for product in products:
        correct_image = resolve_image(product["name"])
        old_image = product["image"] or "(none)"

        if old_image != correct_image:
            cursor.execute(
                "UPDATE products SET image = %s WHERE id = %s",
                (correct_image, product["id"])
            )
            print(f"  ✅ [{product['id']}] {product['name']}")
            print(f"     {old_image} → {correct_image}")
            updated += 1
        else:
            print(f"  ⏭️  [{product['id']}] {product['name']} — already correct")

    conn.commit()
    cursor.close()
    conn.close()
    print(f"\n🎉 Done! Updated {updated} of {len(products)} products.")

if __name__ == "__main__":
    fix_images()
