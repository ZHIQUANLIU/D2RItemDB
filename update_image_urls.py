import sqlite3

DB_PATH = "d2r_items.db"

# D2R物品图片的URL来源
# 这些是一些可能包含D2R物品图片的公开来源
IMAGE_SOURCES = [
    # 可以添加更多来源
]

def update_image_urls():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取现有映射
    cursor.execute("SELECT code FROM item_images")
    codes = [r[0] for r in cursor.fetchall()]
    
    # 为每个code尝试多个可能的URL
    url_patterns = [
        "https://diablo.wiki.gg/images/{code}.png",
        "https://diablo2.diablo.wiki/images/{code}.png", 
        "/static/items/{code}.png",
    ]
    
    updated = 0
    for code in codes:
        for pattern in url_patterns:
            url = pattern.format(code=code)
            cursor.execute("""
                INSERT OR REPLACE INTO item_images (code, image_url, width, height)
                SELECT ?, ?, width, height FROM item_images WHERE code = ?
            """, (code, url, code))
            updated += 1
    
    conn.commit()
    print(f"Updated {updated} image URLs")
    
    conn.close()

if __name__ == "__main__":
    update_image_urls()
