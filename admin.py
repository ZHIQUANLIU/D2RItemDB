from flask import Flask, render_template_string, request, g, session, redirect, url_for, send_from_directory
import sqlite3
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'd2r_admin_secret'

DB_PATH = "d2r_items.db"
UPLOAD_FOLDER = 'static/items'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'original'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'icon'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

TRANSLATIONS = {
    'weapon_types': {
        'axe': '斧子', 'sword': '剑', 'bow': '弓', 'crossbow': '弩',
        'mace': '锤', 'staff': '法杖', 'wand': '魔杖', 'scepter': '权杖',
        'spear': '矛', 'polearm': '长柄', 'dagger': '匕首', 'javelin': '标枪',
    },
    'armor_types': {
        'tors': '衣服', 'helm': '头盔', 'shie': '盾牌', 'belt': '腰带',
        'glov': '手套', 'boot': '靴子', 'circ': '项链', 'pelt': '护符',
    },
    'properties': {
        'str': '力量', 'dex': '敏捷', 'vit': '体力', 'ene': '能量',
        'att': '攻击', 'dmg': '伤害', 'fire': '火焰', 'ltng': '闪电',
        'cold': '冰寒', 'pois': '毒素', 'res-all': '全抗', 'ac': '防御',
    },
    'ui': {
        'title': 'D2R Admin - 图片管理',
        'items': '物品管理',
        'images': '图片管理',
        'upload': '上传图片',
        'search': '搜索',
        'save': '保存',
        'cancel': '取消',
        'delete': '删除',
        'original': '原图',
        'icon': '图标',
        'preview': '预览',
        'no_image': '无图片',
    }
}

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

ADMIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ t.title }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #0a0a14; color: #ccc; min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        
        h1 { color: #f0c040; margin-bottom: 20px; }
        
        .nav { display: flex; gap: 10px; margin-bottom: 20px; }
        .nav a { padding: 10px 20px; background: #1a1a30; color: #888; text-decoration: none; border-radius: 6px; }
        .nav a.active { background: #f0c040; color: #000; }
        
        .toolbar { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .search-box { display: flex; gap: 8px; flex: 1; }
        .search-box input { flex: 1; padding: 10px; border: 1px solid #333; border-radius: 6px; background: #1a1a30; color: #ccc; }
        .btn { padding: 10px 20px; background: #e94560; color: white; border: none; border-radius: 6px; cursor: pointer; }
        .btn:hover { background: #ff6b6b; }
        .btn-secondary { background: #333; }
        .btn-secondary:hover { background: #444; }
        .btn-success { background: #2ecc71; }
        
        .upload-zone { 
            border: 2px dashed #333; border-radius: 10px; padding: 30px; 
            text-align: center; margin-bottom: 20px; background: #151525;
        }
        .upload-zone:hover { border-color: #f0c040; }
        
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 15px; }
        
        .card { background: #1a1a30; border-radius: 8px; padding: 15px; border: 1px solid #333; }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .card-title { color: #f0c040; font-weight: bold; font-size: 1.1em; }
        .card-code { color: #666; font-size: 0.85em; background: #0a0a14; padding: 2px 8px; border-radius: 4px; }
        
        .image-section { margin: 10px 0; }
        .image-label { font-size: 0.85em; color: #888; margin-bottom: 5px; }
        .image-preview { display: flex; gap: 10px; align-items: flex-start; }
        .image-box { 
            flex: 1; background: #0a0a14; border-radius: 6px; padding: 10px; 
            text-align: center; min-height: 100px;
        }
        .image-box img { max-width: 100%; max-height: 80px; }
        .image-box.empty { display: flex; align-items: center; justify-content: center; color: #444; }
        
        .form-group { margin: 10px 0; }
        .form-group label { display: block; font-size: 0.85em; color: #888; margin-bottom: 5px; }
        .form-group input[type="text"] { 
            width: 100%; padding: 8px; border: 1px solid #333; 
            border-radius: 4px; background: #0a0a14; color: #ccc; 
        }
        
        .tabs { display: flex; gap: 5px; margin-bottom: 15px; }
        .tab { padding: 8px 16px; background: #1a1a30; border: none; border-radius: 6px; color: #777; cursor: pointer; }
        .tab.active { background: #f0c040; color: #000; }
        
        .pagination { display: flex; gap: 5px; justify-content: center; margin-top: 20px; }
        .pagination a { padding: 8px 12px; background: #1a1a30; color: #888; text-decoration: none; border-radius: 4px; }
        .pagination a.active { background: #f0c040; color: #000; }
        
        .message { padding: 10px 20px; border-radius: 6px; margin-bottom: 20px; }
        .message.success { background: #2ecc71; color: white; }
        .message.error { background: #e74c3c; color: white; }
        
        .category-badge { 
            display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; 
            margin-right: 5px;
        }
        .category-weapon { background: #e94560; color: white; }
        .category-armor { background: #4a90d9; color: white; }
        .category-unique { background: #ffd700; color: black; }
        .category-set { background: #32cd32; color: white; }
        .category-misc { background: #9370db; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{ t.title }}</h1>
        
        {% if message %}
        <div class="message {{ message_type }}">{{ message }}</div>
        {% endif %}
        
        <div class="nav">
            <a href="/admin/images" class="{{ 'active' if page == 'images' else '' }}">{{ t.images }}</a>
            <a href="/admin/upload" class="{{ 'active' if page == 'upload' else '' }}">{{ t.upload }}</a>
        </div>
        
        {% if page == 'images' %}
        <div class="toolbar">
            <form method="get" class="search-box">
                <input type="text" name="q" placeholder="{{ t.search }}..." value="{{ request.args.get('q', '') }}">
                <select name="category" style="padding: 10px; background: #1a1a30; color: #ccc; border: 1px solid #333; border-radius: 6px;">
                    <option value="">All</option>
                    <option value="weapons" {% if request.args.get('category')=='weapons' %}selected{% endif %}>Weapons</option>
                    <option value="armor" {% if request.args.get('category')=='armor' %}selected{% endif %}>Armor</option>
                    <option value="unique" {% if request.args.get('category')=='unique' %}selected{% endif %}>Unique</option>
                    <option value="set" {% if request.args.get('category')=='set' %}selected{% endif %}>Set</option>
                    <option value="misc" {% if request.args.get('category')=='misc' %}selected{% endif %}>Misc</option>
                </select>
                <button type="submit" class="btn">{{ t.search }}</button>
            </form>
        </div>
        
        <div class="tabs">
            <a href="?{{ build_query('tab', 'all') }}" class="tab {{ 'active' if not request.args.get('tab') or request.args.get('tab')=='all' }}">All</a>
            <a href="?{{ build_query('tab', 'no_image') }}" class="tab {{ 'active' if request.args.get('tab')=='no_image' }}">{{ t.no_image }}</a>
            <a href="?{{ build_query('tab', 'has_image') }}" class="tab {{ 'active' if request.args.get('tab')=='has_image' }}">Has Image</a>
        </div>
        
        <form method="post">
        <div class="grid">
            {% for item in items %}
            <div class="card">
                <div class="card-header">
                    <div>
                        <span class="card-title">{{ item.name }}</span>
                        <span class="category-badge category-{{ item.category }}">{{ item.category }}</span>
                    </div>
                    <span class="card-code">{{ item.code }}</span>
                </div>
                
                <div class="image-section">
                    <div class="image-label">{{ t.original }} (Original)</div>
                    <div class="image-preview">
                        <div class="image-box {{ 'empty' if not item.original_image }}">
                            {% if item.original_image %}
                            <img src="{{ item.original_image }}" alt="Original">
                            {% else %}
                            No Image
                            {% endif %}
                        </div>
                        <input type="text" name="original_{{ item.code }}" value="{{ item.original_image or '' }}" placeholder="URL or leave empty">
                    </div>
                </div>
                
                <div class="image-section">
                    <div class="image-label">{{ t.icon }} (Icon)</div>
                    <div class="image-preview">
                        <div class="image-box {{ 'empty' if not item.icon_image }}">
                            {% if item.icon_image %}
                            <img src="{{ item.icon_image }}" alt="Icon">
                            {% else %}
                            No Image
                            {% endif %}
                        </div>
                        <input type="text" name="icon_{{ item.code }}" value="{{ item.icon_image or '' }}" placeholder="URL or leave empty">
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <div style="margin-top: 20px;">
            <button type="submit" name="save_all" class="btn btn-success">{{ t.save }} All</button>
        </div>
        </form>
        
        {% if total_pages > 1 %}
        <div class="pagination">
            {% if page_num > 1 %}
            <a href="?{{ build_query('page', page_num-1) }}">&lt;</a>
            {% endif %}
            {% for p in range(1, total_pages+1) %}
            <a href="?{{ build_query('page', p) }}" {{ 'class=active' if p == page_num }}>{{ p }}</a>
            {% endfor %}
            {% if page_num < total_pages %}
            <a href="?{{ build_query('page', page_num+1) }}">&gt;</a>
            {% endif %}
        </div>
        {% endif %}
        
        {% elif page == 'upload' %}
        <form method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label>Select Category</label>
                <select name="category" style="padding: 10px; width: 100%; background: #1a1a30; color: #ccc; border: 1px solid #333; border-radius: 6px;">
                    <option value="weapons">Weapons</option>
                    <option value="armor">Armor</option>
                    <option value="misc">Misc</option>
                    <option value="gems">Gems</option>
                </select>
            </div>
            
            <div class="upload-zone">
                <input type="file" name="file" accept="image/*" style="margin: 20px;">
                <input type="text" name="code" placeholder="Item Code (e.g., hax, axe)" style="padding: 10px; width: 200px;">
                <select name="image_type" style="padding: 10px; background: #1a1a30; color: #ccc; border: 1px solid #333;">
                    <option value="original">{{ t.original }}</option>
                    <option value="icon">{{ t.icon }}</option>
                </select>
                <button type="submit" name="upload" class="btn">{{ t.upload }}</button>
            </div>
        </form>
        
        <h3>Quick Reference - Item Codes</h3>
        <div class="grid">
            {% for code in common_codes %}
            <div class="card" style="padding: 10px;">
                <span class="card-code">{{ code }}</span>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

def build_query(key, value, request_obj=None):
    if request_obj is None:
        request_obj = request
    args = dict(request_obj.args)
    args[key] = value
    return '&'.join(f'{k}={v}' for k, v in args.items() if v)

@app.context_processor
def inject():
    return dict(build_query=lambda k, v: build_query(k, v), t=TRANSLATIONS['ui'], min=min, max=max, range=range)

def get_all_items(category='', q='', tab='all', limit=50, offset=0):
    db = get_db()
    items = []
    
    where_clauses = []
    params = []
    
    if q:
        where_clauses.append("(name LIKE ? OR code LIKE ?)")
        params.extend([f'%{q}%', f'%{q}%'])
    
    # Get items from different tables
    if category in ('', 'weapons'):
        if category == '' or category == 'weapons':
            sql = "SELECT code, name, 'weapons' as category FROM weapons WHERE 1=1"
            if q:
                sql += " AND (name LIKE ? OR code LIKE ?)"
            cursor = db.execute(sql, params[:2] if q else [])
            for row in cursor.fetchall():
                items.append({'code': row[0], 'name': row[1], 'category': row[2]})
    
    if category in ('', 'armor'):
        if category == '' or category == 'armor':
            sql = "SELECT code, name, 'armor' as category FROM armor WHERE 1=1"
            if q:
                sql += " AND (name LIKE ? OR code LIKE ?)"
            cursor = db.execute(sql, params[:2] if q else [])
            for row in cursor.fetchall():
                items.append({'code': row[0], 'name': row[1], 'category': row[2]})
    
    if category in ('', 'unique'):
        if category == '' or category == 'unique':
            sql = "SELECT code, name, 'unique' as category FROM unique_items WHERE 1=1"
            if q:
                sql += " AND (name LIKE ? OR code LIKE ?)"
            cursor = db.execute(sql, params[:2] if q else [])
            for row in cursor.fetchall():
                items.append({'code': row[0], 'name': row[1], 'category': row[2]})
    
    if category in ('', 'set'):
        if category == '' or category == 'set':
            sql = "SELECT code, name, 'set' as category FROM set_items WHERE 1=1"
            if q:
                sql += " AND (name LIKE ? OR code LIKE ?)"
            cursor = db.execute(sql, params[:2] if q else [])
            for row in cursor.fetchall():
                items.append({'code': row[0], 'name': row[1], 'category': row[2]})
    
    if category in ('', 'misc'):
        if category == '' or category == 'misc':
            sql = "SELECT code, name, 'misc' as category FROM misc WHERE 1=1"
            if q:
                sql += " AND (name LIKE ? OR code LIKE ?)"
            cursor = db.execute(sql, params[:2] if q else [])
            for row in cursor.fetchall():
                items.append({'code': row[0], 'name': row[1], 'category': row[2]})
    
    # Get existing images
    cursor = db.execute("SELECT code, image_url, image_type FROM item_images")
    images = {}
    for row in cursor.fetchall():
        code = row[0]
        if code not in images:
            images[code] = {'original': '', 'icon': ''}
        if row[2] == 'original':
            images[code]['original'] = row[1]
        elif row[2] == 'icon':
            images[code]['icon'] = row[1]
    
    # Add image info to items
    for item in items:
        code = item['code']
        if code in images:
            item['original_image'] = images[code]['original']
            item['icon_image'] = images[code]['icon']
        else:
            item['original_image'] = ''
            item['icon_image'] = ''
    
    # Filter by tab
    if tab == 'no_image':
        items = [i for i in items if not i['original_image'] and not i['icon_image']]
    elif tab == 'has_image':
        items = [i for i in items if i['original_image'] or i['icon_image']]
    
    return items[offset:offset+limit], len(items)

@app.route('/admin/images', methods=['GET', 'POST'])
def admin_images():
    db = get_db()
    message = ''
    message_type = 'success'
    
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    tab = request.args.get('tab', 'all')
    page_num = int(request.args.get('page', 1))
    per_page = 24
    offset = (page_num - 1) * per_page
    
    if request.method == 'POST' and request.form.get('save_all'):
        # Save all image URLs
        for key, value in request.form.items():
            if key.startswith('original_'):
                code = key.replace('original_', '')
                image_type = 'original'
            elif key.startswith('icon_'):
                code = key.replace('icon_', '')
                image_type = 'icon'
            else:
                continue
            
            if value.strip():
                db.execute("""
                    INSERT OR REPLACE INTO item_images (code, image_url, image_type)
                    VALUES (?, ?, ?)
                """, (code, value.strip(), image_type))
            else:
                db.execute("""
                    DELETE FROM item_images WHERE code = ? AND image_type = ?
                """, (code, image_type))
        
        db.commit()
        message = 'Images saved successfully!'
    
    # Get items
    items, total = get_all_items(category, q, tab, per_page, offset)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    
    return render_template_string(ADMIN_HTML, 
                                  page='images', 
                                  items=items,
                                  page_num=page_num,
                                  total_pages=total_pages,
                                  message=message,
                                  message_type=message_type,
                                  request=request)

@app.route('/admin/upload', methods=['GET', 'POST'])
def admin_upload():
    db = get_db()
    message = ''
    message_type = 'success'
    
    # Common item codes for reference
    cursor = db.execute("SELECT code FROM weapons LIMIT 20")
    common_codes = [r[0] for r in cursor.fetchall()]
    
    if request.method == 'POST' and request.form.get('upload'):
        file = request.files.get('file')
        code = request.form.get('code', '').strip()
        image_type = request.form.get('image_type', 'original')
        
        if not code:
            message = 'Please enter item code'
            message_type = 'error'
        elif file and allowed_file(file.filename):
            filename = secure_filename(f"{code}_{image_type}.{file.filename.rsplit('.', 1)[1].lower()}")
            
            subfolder = 'original' if image_type == 'original' else 'icon'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
            file.save(filepath)
            
            url_path = f"/static/items/{subfolder}/{filename}"
            
            db.execute("""
                INSERT OR REPLACE INTO item_images (code, image_url, image_type)
                VALUES (?, ?, ?)
            """, (code, url_path, image_type))
            db.commit()
            
            message = f'Uploaded {filename} successfully!'
        else:
            message = 'Invalid file or no file selected'
            message_type = 'error'
    
    return render_template_string(ADMIN_HTML, 
                                  page='upload',
                                  common_codes=common_codes,
                                  message=message,
                                  message_type=message_type,
                                  request=request)

@app.route('/admin')
def admin():
    return redirect(url_for('admin_images'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
