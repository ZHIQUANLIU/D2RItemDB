import sqlite3
import os

DB_PATH = "d2r_items.db"

def add_image_support():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建物品图片表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_images (
            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE,
            image_url TEXT,
            width INTEGER DEFAULT 28,
            height INTEGER DEFAULT 28
        )
    """)
    
    # 从各物品表获取code和尺寸
    tables = [
        ('weapons', 'code', 'invwidth', 'invheight'),
        ('armor', 'code', 'invwidth', 'invheight'),
    ]
    
    codes = {}
    for table, code_col, w_col, h_col in tables:
        try:
            cursor.execute(f"SELECT {code_col}, {w_col}, {h_col} FROM {table}")
            for row in cursor.fetchall():
                if row[0]:
                    code = row[0].strip()
                    w = row[1] if row[1] else 2
                    h = row[2] if row[2] else 2
                    codes[code] = (w * 28, h * 28)  # D2物品每格28像素
        except Exception as e:
            print(f"Error from {table}: {e}")
    
    # 为每个code生成图片映射
    # 使用多个可能的图片来源
    for code, dims in codes.items():
        width, height = dims
        # 尝试多个图片源
        urls = [
            # 可以添加更多图片源
            f"/static/items/{code}.png",  # 本地路径
        ]
        
        cursor.execute("""
            INSERT OR IGNORE INTO item_images (code, image_url, width, height)
            VALUES (?, ?, ?, ?)
        """, (code, urls[0], width, height))
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM item_images")
    count = cursor.fetchone()[0]
    print(f"Created {count} item image mappings")
    
    conn.close()
    
    # 创建静态图片目录
    os.makedirs("static/items", exist_ok=True)
    print("Created static/items directory")
    print("\nTo add real item images:")
    print("1. Get item icon PNGs from game files or online")
    print("2. Put images in static/items/ directory")
    print("   Filename should match item code, e.g., hax.png, axe.png")
    print("\nItem code examples:")
    print("- Weapons: hax, axe, swor, bow")
    print("- Armor: cap, helm, tors")

if __name__ == "__main__":
    add_image_support()
