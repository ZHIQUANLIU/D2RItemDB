from flask import render_template, Flask, request, g, session, jsonify, send_from_directory, redirect, url_for, flash
import sqlite3
import json
import os
import base64
import secrets
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv
from whitenoise import WhiteNoise

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Use secure secret key from environment or generate one
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SETTINGS_FILE'] = 'settings.json'

# Security settings
if os.getenv('ENVIRONMENT') == 'production':
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Use WhiteNoise for efficient static serving in production
    app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')
    # Also handle the uploads folder within static
    if os.path.exists('static/uploads'):
        app.wsgi_app.add_files('static/uploads/', prefix='static/uploads/')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_PATH = os.getenv('DATABASE_URL', 'd2r_items.db').replace('sqlite:///', '')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def safe_int(value, default=1, min_val=-1000000, max_val=1000000):
    """Safely convert value to integer with bounds checking"""
    try:
        if value is None: return default
        val = int(value)
        return max(min_val, min(val, max_val))
    except (ValueError, TypeError):
        return default

def safe_str(value, max_length=1000):
    """Safely convert value to string with length limit"""
    if value is None:
        return ""
    return str(value).strip()[:max_length]

def init_db():
    """Initialize database tables if they don't exist"""
    db = get_db()
    cursor = db.cursor()

    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create my_items table with user_id
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS my_items (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            item_type TEXT,
            item_id TEXT,
            account TEXT,
            character_name TEXT,
            storage_type TEXT,
            storage_name TEXT,
            notes TEXT,
            image_path TEXT,
            is_ethereal INTEGER DEFAULT 0,
            is_artifact INTEGER DEFAULT 0,
            sockets INTEGER,
            req_level INTEGER,
            req_str INTEGER,
            req_dex INTEGER,
            defense INTEGER,
            enhanced_defense INTEGER,
            durability INTEGER,
            damage_min INTEGER,
            damage_max INTEGER,
            str_bonus INTEGER,
            dex_bonus INTEGER,
            vit_bonus INTEGER,
            ene_bonus INTEGER,
            life INTEGER,
            mana INTEGER,
            skill_name TEXT,
            skill_level INTEGER,
            ctc_trigger TEXT,
            ctc_skill_name TEXT,
            ctc_skill_level INTEGER,
            ias INTEGER,
            fcr INTEGER,
            fhr INTEGER,
            frw INTEGER,
            res_fire INTEGER,
            res_cold INTEGER,
            res_ltng INTEGER,
            res_pois INTEGER,
            res_all INTEGER,
            absorb_fire INTEGER,
            absorb_cold INTEGER,
            absorb_ltng INTEGER,
            add_fire_min INTEGER,
            add_fire_max INTEGER,
            add_cold_min INTEGER,
            add_cold_max INTEGER,
            add_ltng_min INTEGER,
            add_ltng_max INTEGER,
            add_pois_min INTEGER,
            add_pois_max INTEGER,
            mf INTEGER,
            eg INTEGER,
            life_steal REAL,
            mana_steal REAL,
            life_after_kill INTEGER,
            mana_after_kill INTEGER,
            attack_rating INTEGER,
            attack_rating_plus INTEGER,
            crushing_blow INTEGER,
            deadly_strike INTEGER,
            open_wounds INTEGER,
            cannot_be_frozen INTEGER DEFAULT 0,
            ctc_trigger2 TEXT,
            ctc_skill_name2 TEXT,
            ctc_skill_level2 INTEGER,
            ctc_trigger3 TEXT,
            ctc_skill_name3 TEXT,
            ctc_skill_level3 INTEGER,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Create image cache table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_cache (
            id INTEGER PRIMARY KEY,
            file_hash TEXT UNIQUE NOT NULL,
            image_url TEXT,
            item_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create accounts table (if not exists)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            notes TEXT,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    # Create item_images table for the admin utility
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS item_images (
            id INTEGER PRIMARY KEY,
            code TEXT NOT NULL,
            image_url TEXT NOT NULL,
            image_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(code, image_type)
        )
    """)

    # Add indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_my_items_user ON my_items(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_my_items_account ON my_items(account)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_my_items_storage ON my_items(storage_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_my_items_create_time ON my_items(create_time DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_user ON characters(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_image_cache_hash ON image_cache(file_hash)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_images_code ON item_images(code)")

    db.commit()

# Initialize database on first request
@app.before_request
def setup():
    if not hasattr(g, '_db_initialized'):
        init_db()
        g._db_initialized = True

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def load_settings():
    if os.path.exists(app.config['SETTINGS_FILE']):
        with open(app.config['SETTINGS_FILE'], 'r') as f:
            settings = json.load(f)
    else:
        settings = {}

    # Override with environment variables (take precedence)
    settings['gemini_api_key'] = os.getenv('GEMINI_API_KEY', settings.get('gemini_api_key', ''))
    settings['ocr_method'] = os.getenv('OCR_METHOD', settings.get('ocr_method', 'easyocr'))

    return settings

def save_settings(settings):
    # Don't save API key to file - only save non-sensitive settings
    safe_settings = {k: v for k, v in settings.items() if k != 'gemini_api_key'}
    with open(app.config['SETTINGS_FILE'], 'w') as f:
        json.dump(safe_settings, f)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')

        # Check against database
        user = query_db("SELECT id, password FROM users WHERE username = ?", (username,), one=True)

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session.permanent = True
            next_url = request.args.get('next', '/')
            return redirect(next_url)

        flash('用户名或密码错误', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')

        if len(username) < 3 or len(password) < 6:
            flash('用户名至少3个字符，密码至少6个字符', 'error')
            return render_template('register.html')

        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            db.commit()
            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('用户名已存在', 'error')

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    lang = request.args.get('lang', 'zh')
    if request.method == 'POST':
        gemini_key = request.form.get('gemini_api_key', '').strip()
        ocr_method = request.form.get('ocr_method', 'gemini')
        save_settings({'gemini_api_key': gemini_key, 'ocr_method': ocr_method})
        return f'<script>alert("Settings saved!"); window.location.href="/?lang={lang}";</script>'
    
    s = load_settings()
    return render_template('settings.html', lang=lang, s=s)

# 账户管理
@app.route('/accounts', methods=['GET', 'POST'])
def manage_accounts():
    lang = request.args.get('lang', 'zh')
    db = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_account':
            name = request.form.get('account_name', '').strip()
            notes = request.form.get('notes', '')
            if name:
                try:
                    db.execute('INSERT INTO accounts (name, notes) VALUES (?, ?)', (name, notes))
                    db.commit()
                except:
                    pass
        elif action == 'add_character':
            account_id = request.form.get('account_id')
            char_name = request.form.get('char_name', '').strip()
            char_class = request.form.get('char_class', '')
            if account_id and char_name:
                try:
                    db.execute('INSERT INTO characters (account_id, name, class) VALUES (?, ?, ?)', (account_id, char_name, char_class))
                    db.commit()
                except:
                    pass
        elif action == 'delete_account':
            account_id = request.form.get('account_id')
            db.execute('DELETE FROM characters WHERE account_id = ?', (account_id,))
            db.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
            db.commit()
        elif action == 'delete_character':
            char_id = request.form.get('char_id')
            db.execute('DELETE FROM characters WHERE id = ?', (char_id,))
            db.commit()
    
    accounts = query_db('SELECT * FROM accounts ORDER BY name')
    characters = query_db('SELECT c.*, a.name as account_name FROM characters c JOIN accounts a ON c.account_id = a.id ORDER BY a.name, c.name')
    
    return render_template('accounts.html', accounts=accounts, characters=characters, lang=lang)

# 'accounts.html' moved to templates/accounts.html

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload-item-image', methods=['POST'])
def upload_item_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        import uuid
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file.save(filepath)
        
        try:
            settings = load_settings()
            ocr_method = settings.get('ocr_method', 'easyocr')
            
            if ocr_method == 'gemini':
                gemini_key = settings.get('gemini_api_key', '')
                if not gemini_key:
                    return jsonify({'error': 'Gemini API key not configured. Go to /settings'}), 400
                item_data = extract_with_gemini(filepath, gemini_key)
            else:
                from ocr_utils import extract_item_from_image
                item_data = extract_item_from_image(filepath)
            
            return jsonify({
                'success': True,
                'image_url': f'/static/uploads/{filename}',
                'item_data': item_data
            })
        except Exception as e:
            import traceback
            return jsonify({'error': f'{str(e)}'}), 500
    
    return jsonify({'error': 'Invalid file type'}), 400

def extract_with_gemini(image_path, api_key):
    import google.generativeai as genai
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    
    with open(image_path, 'rb') as f:
        image_data = f.read()
    
    prompt = '''Extract Diablo 2 Resurrected item stats from this image. Return ONLY a JSON object with these exact fields:
{
  "item_name": "item name",
  "item_color": "unique|set|magic|rare|craft|normal",
  "req_level": number,
  "req_str": number, 
  "req_dex": number,
  "defense": number,
  "enhanced_defense": number,
  "sockets": number,
  "durability": [current, max],
  "damage_min": number,
  "damage_max": number,
  "str_bonus": number,
  "dex_bonus": number,
  "vit_bonus": number,
  "ene_bonus": number,
  "life": number,
  "mana": number,
  "skill_name": "skill name",
  "skill_level": number,
  "ias": number,
  "fcr": number,
  "fhr": number,
  "frw": number,
  "res_fire": number,
  "res_cold": number,
  "res_ltng": number,
  "res_pois": number,
  "res_all": number,
  "mf": number,
  "eg": number,
  "life_steal": number,
  "mana_steal": number,
  "life_after_kill": number,
  "mana_after_kill": number,
  "attack_rating": number,
  "attack_rating_plus": number,
  "crushing_blow": number,
  "deadly_strike": number,
  "open_wounds": number,
  "cannot_be_frozen": 1 or 0,
  "is_ethereal": 1 or 0,
  "experience": number,
  "target_defense": number,
  "other_stats": ["list of other stats found"]
}
If a stat is not present or cannot be determined, use null. For ranges like "10-20 damage", parse min and max separately.'''
    
    image_part = {'mime_type': 'image/jpeg', 'data': base64.b64encode(image_data).decode('utf-8')}
    response = model.generate_content([prompt, image_part])
    
    text = response.text
    text = text.replace('```json', '').replace('```', '').strip()
    
    return json.loads(text)
    
    return jsonify({'error': 'Invalid file type'}), 400

TRANSLATIONS = {
    'weapon_types': {
        'axe': '斧子', 'sword': '剑', 'bow': '弓', 'crossbow': '弩',
        'mace': '锤', 'staff': '法杖', 'wand': '魔杖', 'scepter': '权杖',
        'spear': '矛', 'polearm': '长柄', 'dagger': '匕首', 'javelin': '标枪',
        'throwing': '投掷', 'orb': '球', 'h2h': '拳套', 'hamm': '锤',
        'abow': '亚马逊弓', 'ajav': '亚马逊标枪', 'aspe': '亚马逊矛',
        'tkni': '飞刀', 'tpot': '投掷斧', 'taxe': '野蛮人斧'
    },
    'armor_types': {
        'tors': '衣服', 'helm': '头盔', 'shie': '盾牌', 'belt': '腰带',
        'glov': '手套', 'boot': '靴子', 'circ': '项链', 'pelt': '护符',
        'head': '头部', 'ashd': '亚马逊盾牌', 'phlm': '神圣之盾', 'grim': '死亡面具'
    },
    'properties': {
        'str': '力量', 'dex': '敏捷', 'vit': '体力', 'ene': '能量',
        'att': '攻击', 'att%': '攻击%', 'dmg': '伤害', 'dmg%': '伤害%',
        'mindam': '最小伤害', 'maxdam': '最大伤害', 'fire': '火焰',
        'fire-min': '最小火焰', 'fire-max': '最大火焰', 'ltng': '闪电',
        'ltng-min': '最小闪电', 'ltng-max': '最大闪电', 'cold': '冰寒',
        'cold-min': '最小冰寒', 'cold-max': '最大冰寒', 'pois': '毒素',
        'pois-min': '最小毒素', 'pois-max': '最大毒素', 'res-all': '全抗性',
        'res-fire': '火抗', 'res-ltng': '电抗', 'res-cold': '冰抗', 'res-pois': '毒抗',
        'ac': '防御', 'ac%': '防御%', 'maxac': '最大防御', 'block': '格挡',
        'durability': '耐久', 'speed': '速度', 'reqstr': '力量需求', 'reqdex': '敏捷需求',
        'sockets': '孔数', 'level': '等级', 'levelreq': '等级需求',
        'life': '生命', 'mana': '魔法', 'regen': '生命恢复', 'regen-mana': '魔法恢复',
        'lifesteal': '生命偷取', 'manasteal': '魔法偷取', 'crush': '压碎',
        'deadly': '致命', 'openwounds': '撕裂', 'chance': '概率',
        'ctc': '概率触发', 'skill': '技能', 'allskills': '全技能',
        'aura': '光环', 'item': '物品', 'rep': '持续时间',
        'thorns': '荆棘', 'hit-skill': '击中触发', 'gethit-skill': '受击触发',
        'kill-skill': '击杀触发', 'ow': '撕裂伤口', 'cb': '压碎打击',
        'ias': '攻速', 'fcr': '施法速度', 'fhr': '格挡恢复', 'frw': '跑速',
        'mdmg': '魔法伤害', 'fdmg': '火焰伤害', 'ldmg': '闪电伤害',
        'pdmg': '毒素伤害', 'reduce': '减少', 'dmg-to-mana': '伤害转魔',
        'slow': '减速', 'knock': '击退', 'freeze': '冻结', 'howl': '尖叫',
        'stupidity': '痴呆', 'lure': '诱惑', 'dim': '失明', 'grad': '偷取',
        'red-mag': '魔法消耗', 'ease': '需求降低', 'Ber': '符文', 'Sha': '符文',
        'charged': '充能'
    },
    'ui': {
        'search': '搜索',
        'search_placeholder': '搜索物品名称...',
        'all': '全部', 'weapons': '武器', 'armor': '护甲',
        'unique': '暗金', 'set': '套装', 'misc': '杂物',
        'gems': '宝石', 'runes': '符文',
        'damage': '伤害', 'defense': '防御', 'defence': '防御',
        'level': '等级', 'req': '需求', 'speed': '速度',
        'str': '力量', 'dex': '敏捷', 'dur': '耐久',
        'sockets': '孔', 'price': '价格',
        'gamble': '赌博', 'rarity': '稀有度', 'magic': '魔法',
        'block': '格挡', 'type': '类型', 'weapon_type': '武器类型',
        'armor_type': '护甲类型', 'sort_by': '排序',
        'raw_data': '原始数据', 'set_bonus': '套装', 'rune': '符文',
        'filter': '筛选', 'result_count': '共 {count} 件物品'
    }
}

def get_translation(key, lang='zh'):
    if lang == 'en':
        return key
    return TRANSLATIONS.get(key, {})

def translate_item_type(item_type, lang='zh'):
    if not item_type:
        return ''
    if lang == 'en':
        return item_type
    weapon_map = TRANSLATIONS['weapon_types']
    armor_map = TRANSLATIONS['armor_types']
    combined = {**weapon_map, **armor_map}
    return combined.get(item_type, item_type)

def translate_prop(prop, lang='zh'):
    if not prop:
        return prop
    if lang == 'en':
        return prop
    prop_map = TRANSLATIONS['properties']
    for k, v in prop_map.items():
        if k.lower() in prop.lower():
            return prop.replace(k, v).replace(k.upper(), v)
    return prop

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def get_item_image(code):
    try:
        db = get_db()
        cursor = db.execute("SELECT image_url FROM item_images WHERE code = ?", (code,))
        row = cursor.fetchone()
        return row[0] if row else ''
    except:
        return ''

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def row_to_dict(row):
    d = dict(row)
    if 'raw_data' in d and d['raw_data']:
        try:
            raw = json.loads(d['raw_data'])
            for k, v in raw.items():
                if k not in d:
                    d[k] = v
        except:
            pass
    # 添加图片URL
    if 'code' in d and d['code']:
        d['image_url'] = get_item_image(d['code'])
    return d

def get_sort_order(sort, category):
    if category == 'gems':
        if sort == 'level':
            return 'level ASC'
        elif sort == 'level_desc':
            return 'level DESC'
        elif sort == 'name':
            return 'name ASC'
        return 'level ASC'
    
    if category == 'runes':
        if sort == 'name':
            return 'name ASC'
        return 'name ASC'
    
    if category in ('misc', 'unique', 'set'):
        if sort == 'level':
            return 'level ASC, levelreq ASC'
        elif sort == 'level_desc':
            return 'level DESC, levelreq DESC'
        elif sort == 'cost':
            return 'cost ASC'
        elif sort == 'cost_desc':
            return 'cost DESC'
        elif sort == 'name':
            return 'name ASC'
        return 'level ASC'
    
    if sort == 'level':
        return 'level ASC, levelreq ASC'
    elif sort == 'level_desc':
        return 'level DESC, levelreq DESC'
    elif sort == 'damage':
        return 'mindam ASC, maxdam ASC'
    elif sort == 'damage_desc':
        return 'mindam DESC, maxdam DESC'
    elif sort == 'defense':
        return 'minac ASC, maxac ASC'
    elif sort == 'defense_desc':
        return 'minac DESC, maxac DESC'
    elif sort == 'cost':
        return 'cost ASC'
    elif sort == 'cost_desc':
        return 'cost DESC'
    elif sort == 'name':
        return 'name ASC'
    return 'level ASC'

# 'index.html' moved to templates/index.html

def build_query(key, value):
    args = request.args.copy()
    args[key] = value
    return '&'.join(f'{k}={v}' for k, v in args.items())

@app.context_processor
def inject_helpers():
    return dict(build_query=build_query, translate_type=translate_item_type, translate_prop=translate_prop, 
                min=min, max=max, range=range)

def build_search_conditions(q, table_prefix=""):
    """Build search conditions for parameterized queries"""
    conditions = []
    params = []

    if q:
        if table_prefix in ('unique', 'set'):
            # Special handling for unique/set items with multiple name fields
            conditions.append("(name LIKE ? OR index_name LIKE ?)")
            if table_prefix == 'set':
                conditions.append("OR set_name LIKE ?")
            params.extend([f"%{q}%", f"%{q}%"])
            if table_prefix == 'set':
                params.append(f"%{q}%")
        else:
            conditions.append("name LIKE ?")
            params.append(f"%{q}%")

    return conditions, params

def execute_category_query(table_name, category_name, conditions, params, order_by,
                          limit, offset, count_only=False):
    """Execute a parameterized query for a category with proper pagination"""
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    if count_only:
        sql = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"
        result = query_db(sql, tuple(params), one=True)
        return result[0] if result else 0
    else:
        sql = f"SELECT *, '{category_name}' as category FROM {table_name} WHERE {where_clause} ORDER BY {order_by} LIMIT ? OFFSET ?"
        params_with_pagination = params + [limit, offset]
        rows = query_db(sql, tuple(params_with_pagination))
        return [row_to_dict(r) for r in rows]

def get_filtered_items(args):
    """Refactored logic to filter items from multiple tables"""
    q = safe_str(args.get('q', ''))
    category = safe_str(args.get('category', 'all'))
    wtype = safe_str(args.get('wtype', 'all'))
    atype = safe_str(args.get('atype', 'all'))
    sort = safe_str(args.get('sort', 'level'))
    page = safe_int(args.get('page', 1), default=1)
    per_page = safe_int(args.get('per_page', 50), default=50, max_val=500)

    items = []
    total_count = 0
    offset = (page - 1) * per_page

    wtype_map = {
        'axe': ['axe', 'taxe'],
        'sword': ['swor'],
        'bow': ['bow'],
        'crossbow': ['xbow'],
        'mace': ['mace', 'hamm', 'club'],
        'staff': ['staf'],
        'wand': ['wand'],
        'scepter': ['scep'],
        'spear': ['spea', 'aspe'],
        'polearm': ['pole'],
        'dagger': ['knif', 'tkni'],
        'javelin': ['jave', 'ajav']
    }

    # Define category configurations
    categories = {
        'weapons': {'table': 'weapons', 'category_name': 'weapons', 'extra_conditions': [], 'extra_params': []},
        'armor': {'table': 'armor', 'category_name': 'armor', 'extra_conditions': [], 'extra_params': []},
        'unique': {'table': 'unique_items', 'category_name': 'unique', 'extra_conditions': [], 'extra_params': []},
        'set': {'table': 'set_items', 'category_name': 'set', 'extra_conditions': [], 'extra_params': []},
        'misc': {'table': 'misc', 'category_name': 'misc', 'extra_conditions': [], 'extra_params': []},
        'gems': {'table': 'gems', 'category_name': 'gem', 'extra_conditions': [], 'extra_params': []},
        'runes': {'table': 'runes', 'category_name': 'rune', 'extra_conditions': [], 'extra_params': []}
    }

    if wtype != 'all' and wtype in wtype_map:
        categories['weapons']['extra_conditions'].append("type IN ({})".format(','.join('?' * len(wtype_map[wtype]))))
        categories['weapons']['extra_params'].extend(wtype_map[wtype])

    if atype != 'all':
        categories['armor']['extra_conditions'].append("type = ?")
        categories['armor']['extra_params'].append(atype)

    for cat_key, cat_config in categories.items():
        if category not in ('all', cat_key): continue
        search_conditions, search_params = build_search_conditions(q, cat_key if cat_key in ('unique', 'set') else "")
        all_conditions = search_conditions + cat_config['extra_conditions']
        all_params = search_params + cat_config['extra_params']
        order_by = get_sort_order(sort, cat_key)

        cat_items = execute_category_query(cat_config['table'], cat_config['category_name'], all_conditions, all_params, order_by, per_page, offset)
        items.extend(cat_items)
        cat_count = execute_category_query(cat_config['table'], cat_config['category_name'], all_conditions, all_params, order_by, per_page, offset, count_only=True)
        total_count += cat_count

    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
    return {
        'items': items,
        'total_count': total_count,
        'total_pages': total_pages,
        'page': page,
        'per_page': per_page
    }

@app.route('/')
def index():
    lang = safe_str(request.args.get('lang', 'zh'))
    data = get_filtered_items(request.args)
    return render_template('index.html', **data, request=request, lang=lang)

@app.route('/api/items')
def api_items():
    lang = safe_str(request.args.get('lang', 'zh'))
    data = get_filtered_items(request.args)
    # Translate types/props if needed in API? 
    # For now, just return raw data as requested for AJAX integration
    return jsonify(data)

@app.route('/api/item-defaults')
def get_item_defaults():
    name = safe_str(request.args.get('name', ''))
    if not name:
        return jsonify(None)

    db = get_db()
    res = {}

    # Try unique items first
    u = query_db("SELECT * FROM unique_items WHERE name = ?", (name,), one=True)
    if u:
        res['item_type'] = 'unique'
        if u['levelreq']: res['req_level'] = u['levelreq']
        # Try to get base item stats via code
        base = query_db("SELECT * FROM armor WHERE code = ?", (u['code'],), one=True)
        if not base:
            base = query_db("SELECT * FROM weapons WHERE code = ?", (u['code'],), one=True)
        
        if base:
            if 'maxac' in base.keys() and base['maxac']: res['defense'] = base['maxac']
            if 'mindam' in base.keys() and base['mindam']: res['damage_min'] = base['mindam']
            if 'maxdam' in base.keys() and base['maxdam']: res['damage_max'] = base['maxdam']
            if 'reqstr' in base.keys() and base['reqstr']: res['req_str'] = base['reqstr']
            if 'reqdex' in base.keys() and base['reqdex']: res['req_dex'] = base['reqdex']
            if 'gemsockets' in base.keys() and base['gemsockets']: res['sockets'] = base['gemsockets']
            if 'durability' in base.keys() and base['durability']: res['durability'] = base['durability']
        return jsonify(res)

    # Try set items
    s = query_db("SELECT * FROM set_items WHERE name = ?", (name,), one=True)
    if s:
        res['item_type'] = 'set'
        if s['levelreq']: res['req_level'] = s['levelreq']
        base = query_db("SELECT * FROM armor WHERE code = ?", (s['code'],), one=True)
        if not base:
            base = query_db("SELECT * FROM weapons WHERE code = ?", (s['code'],), one=True)
        if base:
            if 'maxac' in base.keys() and base['maxac']: res['defense'] = base['maxac']
            if 'mindam' in base.keys() and base['mindam']: res['damage_min'] = base['mindam']
            if 'maxdam' in base.keys() and base['maxdam']: res['damage_max'] = base['maxdam']
            if 'reqstr' in base.keys() and base['reqstr']: res['req_str'] = base['reqstr']
            if 'reqdex' in base.keys() and base['reqdex']: res['req_dex'] = base['reqdex']
            if 'gemsockets' in base.keys() and base['gemsockets']: res['sockets'] = base['gemsockets']
            if 'durability' in base.keys() and base['durability']: res['durability'] = base['durability']
        return jsonify(res)

    # Try base armor
    a = query_db("SELECT * FROM armor WHERE name = ?", (name,), one=True)
    if a:
        res['item_type'] = 'normal'
        if a['levelreq']: res['req_level'] = a['levelreq']
        if a['maxac']: res['defense'] = a['maxac']
        if a['reqstr']: res['req_str'] = a['reqstr']
        if a['reqdex']: res['req_dex'] = a['reqdex']
        if a['gemsockets']: res['sockets'] = a['gemsockets']
        if a['durability']: res['durability'] = a['durability']
        return jsonify(res)

    # Try base weapons
    w = query_db("SELECT * FROM weapons WHERE name = ?", (name,), one=True)
    if w:
        res['item_type'] = 'normal'
        if w['levelreq']: res['req_level'] = w['levelreq']
        if w['mindam']: res['damage_min'] = w['mindam']
        if w['maxdam']: res['damage_max'] = w['maxdam']
        if w['reqstr']: res['req_str'] = w['reqstr']
        if w['reqdex']: res['req_dex'] = w['reqdex']
        if w['gemsockets']: res['sockets'] = w['gemsockets']
        if w['durability']: res['durability'] = w['durability']
        return jsonify(res)

    return jsonify(None)

# 我的物品管理路由
@app.route('/my-items')
@login_required
def my_items():
    lang = request.args.get('lang', 'zh')
    account = safe_str(request.args.get('account', ''))
    storage_type = safe_str(request.args.get('storage_type', ''))

    user_id = session['user_id']
    where_conditions = ["user_id = ?"]
    params = [user_id]

    if account:
        where_conditions.append("account LIKE ?")
        params.append(f"%{account}%")
    if storage_type:
        where_conditions.append("storage_type = ?")
        params.append(storage_type)

    where_clause = " AND ".join(where_conditions)
    sql = f"SELECT * FROM my_items WHERE {where_clause} ORDER BY create_time DESC"
    items = query_db(sql, tuple(params))

    accounts_sql = "SELECT DISTINCT account FROM my_items WHERE user_id = ? ORDER BY account"
    accounts = [r[0] for r in query_db(accounts_sql, (user_id,))]

    return render_template('my_items.html', items=items, accounts=accounts,
                                selected_account=account, selected_storage=storage_type, lang=lang)

@app.route('/my-items/add', methods=['GET', 'POST'])
@login_required
def my_items_add():
    lang = request.args.get('lang', 'zh')

    if request.method == 'POST':
        def int_or_none(v): return int(v) if v and v.strip() else None
        def float_or_none(v): return float(v) if v and v.strip() else None
        
        item_type = request.form.get('item_type', 'normal')
        item_id = request.form.get('item_id', '')
        account = request.form.get('account', '')
        character_name = request.form.get('character_name', '')
        storage_type = request.form.get('storage_type', '')
        storage_name = request.form.get('storage_name', '')
        notes = request.form.get('notes', '')
        image_path = request.form.get('image_path', '')
        is_ethereal = 1 if request.form.get('is_ethereal') else 0
        is_artifact = 1 if request.form.get('is_artifact') else 0
        sockets = int_or_none(request.form.get('sockets'))
        
        # 属性
        req_level = int_or_none(request.form.get('req_level'))
        req_str = int_or_none(request.form.get('req_str'))
        req_dex = int_or_none(request.form.get('req_dex'))
        defense = int_or_none(request.form.get('defense'))
        enhanced_defense = int_or_none(request.form.get('enhanced_defense'))
        durability = int_or_none(request.form.get('durability'))
        damage_min = int_or_none(request.form.get('damage_min'))
        damage_max = int_or_none(request.form.get('damage_max'))
        
        # 属性加成
        str_bonus = int_or_none(request.form.get('str_bonus'))
        dex_bonus = int_or_none(request.form.get('dex_bonus'))
        vit_bonus = int_or_none(request.form.get('vit_bonus'))
        ene_bonus = int_or_none(request.form.get('ene_bonus'))
        life = int_or_none(request.form.get('life'))
        mana = int_or_none(request.form.get('mana'))
        
        # 技能
        skill_name = request.form.get('skill_name', '')
        skill_level = int_or_none(request.form.get('skill_level'))
        
        # CTC
        ctc_trigger = request.form.get('ctc_trigger', '')
        ctc_skill_name = request.form.get('ctc_skill_name', '')
        ctc_skill_level = int_or_none(request.form.get('ctc_skill_level'))
        
        # 速度
        ias = int_or_none(request.form.get('ias'))
        fcr = int_or_none(request.form.get('fcr'))
        fhr = int_or_none(request.form.get('fhr'))
        frw = int_or_none(request.form.get('frw'))
        
        # 抗性
        res_fire = int_or_none(request.form.get('res_fire'))
        res_cold = int_or_none(request.form.get('res_cold'))
        res_ltng = int_or_none(request.form.get('res_ltng'))
        res_pois = int_or_none(request.form.get('res_pois'))
        res_all = int_or_none(request.form.get('res_all'))
        
        # 吸收
        absorb_fire = int_or_none(request.form.get('absorb_fire'))
        absorb_cold = int_or_none(request.form.get('absorb_cold'))
        absorb_ltng = int_or_none(request.form.get('absorb_ltng'))
        
        # 元素伤害
        add_fire_min = int_or_none(request.form.get('add_fire_min'))
        add_fire_max = int_or_none(request.form.get('add_fire_max'))
        add_cold_min = int_or_none(request.form.get('add_cold_min'))
        add_cold_max = int_or_none(request.form.get('add_cold_max'))
        add_ltng_min = int_or_none(request.form.get('add_ltng_min'))
        add_ltng_max = int_or_none(request.form.get('add_ltng_max'))
        add_pois_min = int_or_none(request.form.get('add_pois_min'))
        add_pois_max = int_or_none(request.form.get('add_pois_max'))
        
        # MF/GF/偷取
        mf_val = int_or_none(request.form.get('mf'))
        eg = int_or_none(request.form.get('eg'))
        life_steal = float_or_none(request.form.get('life_steal'))
        mana_steal = float_or_none(request.form.get('mana_steal'))
        life_after_kill = int_or_none(request.form.get('life_after_kill'))
        mana_after_kill = int_or_none(request.form.get('mana_after_kill'))
        
        # 攻击属性
        attack_rating = int_or_none(request.form.get('attack_rating'))
        attack_rating_plus = int_or_none(request.form.get('attack_rating_plus'))
        crushing_blow = int_or_none(request.form.get('crushing_blow'))
        deadly_strike = int_or_none(request.form.get('deadly_strike'))
        open_wounds = int_or_none(request.form.get('open_wounds'))
        
        cannot_be_frozen = 1 if request.form.get('cannot_be_frozen') else 0
        
        # CTC 2 & 3
        ctc_trigger2 = request.form.get('ctc_trigger2', '')
        ctc_skill_name2 = request.form.get('ctc_skill_name2', '')
        ctc_skill_level2 = int_or_none(request.form.get('ctc_skill_level2'))
        ctc_trigger3 = request.form.get('ctc_trigger3', '')
        ctc_skill_name3 = request.form.get('ctc_skill_name3', '')
        ctc_skill_level3 = int_or_none(request.form.get('ctc_skill_level3'))
        
        db = get_db()
        user_id = session['user_id']
        cols = "user_id, item_type, item_id, account, character_name, storage_type, storage_name, notes, image_path, is_ethereal, is_artifact, sockets, req_level, req_str, req_dex, defense, enhanced_defense, durability, damage_min, damage_max, str_bonus, dex_bonus, vit_bonus, ene_bonus, life, mana, skill_name, skill_level, ctc_trigger, ctc_skill_name, ctc_skill_level, ias, fcr, fhr, frw, res_fire, res_cold, res_ltng, res_pois, res_all, absorb_fire, absorb_cold, absorb_ltng, add_fire_min, add_fire_max, add_cold_min, add_cold_max, add_ltng_min, add_ltng_max, add_pois_min, add_pois_max, mf, eg, life_steal, mana_steal, life_after_kill, mana_after_kill, attack_rating, attack_rating_plus, crushing_blow, deadly_strike, open_wounds, cannot_be_frozen, ctc_trigger2, ctc_skill_name2, ctc_skill_level2, ctc_trigger3, ctc_skill_name3, ctc_skill_level3"
        vals = (user_id, item_type, item_id, account, character_name, storage_type, storage_name, notes, image_path, is_ethereal, is_artifact, sockets, req_level, req_str, req_dex, defense, enhanced_defense, durability, damage_min, damage_max, str_bonus, dex_bonus, vit_bonus, ene_bonus, life, mana, skill_name, skill_level, ctc_trigger, ctc_skill_name, ctc_skill_level, ias, fcr, fhr, frw, res_fire, res_cold, res_ltng, res_pois, res_all, absorb_fire, absorb_cold, absorb_ltng, add_fire_min, add_fire_max, add_cold_min, add_cold_max, add_ltng_min, add_ltng_max, add_pois_min, add_pois_max, mf_val, eg, life_steal, mana_steal, life_after_kill, mana_after_kill, attack_rating, attack_rating_plus, crushing_blow, deadly_strike, open_wounds, cannot_be_frozen, ctc_trigger2, ctc_skill_name2, ctc_skill_level2, ctc_trigger3, ctc_skill_name3, ctc_skill_level3)
        placeholders = '(' + ', '.join(['?'] * len(vals)) + ')'
        db.execute(f'INSERT INTO my_items ({cols}) VALUES {placeholders}', vals)
        db.commit()
        return f'<script>alert("添加成功!"); window.location.href="/my-items?lang={lang}";</script>'
    
    user_id = session['user_id']
    unique_items = [tuple(r) for r in query_db("SELECT index_name, name FROM unique_items ORDER BY index_name")]
    set_items = [tuple(r) for r in query_db("SELECT index_name, set_name FROM set_items ORDER BY index_name")]
    weapons = [tuple(r) for r in query_db("SELECT name, type FROM weapons ORDER BY name")]
    armors = [tuple(r) for r in query_db("SELECT name, type FROM armor ORDER BY name")]
    misc_items = [tuple(r) for r in query_db("SELECT name, type FROM misc ORDER BY name")]
    accounts = [tuple(r) for r in query_db("SELECT id, name FROM accounts WHERE user_id = ? ORDER BY name", (user_id,))]
    characters = [tuple(r) for r in query_db("SELECT id, account_id, name, class FROM characters WHERE user_id = ? ORDER BY name", (user_id,))]

    return render_template('my_items_add.html',
                                  unique_items=unique_items,
                                  set_items=set_items,
                                  weapons=weapons,
                                  armors=armors,
                                  misc_items=misc_items,
                                  accounts=accounts,
                                  characters=characters,
                                  lang=lang)

@app.route('/my-items/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def my_items_edit(item_id):
    lang = request.args.get('lang', 'zh')
    user_id = session['user_id']
    db = get_db()

    # Check if item belongs to user
    item = query_db("SELECT * FROM my_items WHERE id = ? AND user_id = ?", (item_id, user_id), one=True)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    if request.method == 'POST':
        item_type = request.form.get('item_type', 'normal')
        item_id_val = request.form.get('item_id', '')
        account = request.form.get('account', '')
        character_name = request.form.get('character_name', '')
        storage_type = request.form.get('storage_type', '')
        storage_name = request.form.get('storage_name', '')
        notes = request.form.get('notes', '')
        is_ethereal = 1 if request.form.get('is_ethereal') else 0
        is_artifact = 1 if request.form.get('is_artifact') else 0
        quality = safe_int(request.form.get('quality', 0))
        defense = safe_int(request.form.get('defense', 0), default=None)
        enhanced_damage = safe_int(request.form.get('enhanced_damage', 0), default=None)
        skills = safe_int(request.form.get('skills', 0), default=None)
        all_resists = safe_int(request.form.get('all_resists', 0), default=None)
        mf = safe_int(request.form.get('mf', 0), default=None)
        sockets = safe_int(request.form.get('sockets', 0), default=None)

        db.execute('''
            UPDATE my_items SET item_type=?, item_id=?, account=?, character_name=?, storage_type=?, storage_name=?, notes=?, is_ethereal=?, is_artifact=?, quality=?, defense=?, enhanced_damage=?, skills=?, all_resists=?, mf=?, sockets=?, update_time=CURRENT_TIMESTAMP
            WHERE id=? AND user_id=?
        ''', (item_type, item_id_val, account, character_name, storage_type, storage_name, notes, is_ethereal, is_artifact, quality, defense, enhanced_damage, skills, all_resists, mf, sockets, item_id, user_id))
        db.commit()
        return f'<script>alert("更新成功!"); window.location.href="/my-items?lang={lang}";</script>'

    unique_items = [tuple(r) for r in query_db("SELECT index_name, name FROM unique_items ORDER BY index_name")]
    set_items = [tuple(r) for r in query_db("SELECT index_name, set_name FROM set_items ORDER BY index_name")]
    weapons = [tuple(r) for r in query_db("SELECT name, type FROM weapons ORDER BY name")]
    armors = [tuple(r) for r in query_db("SELECT name, type FROM armor ORDER BY name")]
    misc_items = [tuple(r) for r in query_db("SELECT name, type FROM misc ORDER BY name")]
    accounts = [tuple(r) for r in query_db("SELECT id, name FROM accounts WHERE user_id = ? ORDER BY name", (user_id,))]
    characters = [tuple(r) for r in query_db("SELECT id, account_id, name, class FROM characters WHERE user_id = ? ORDER BY name", (user_id,))]

    return render_template('my_items_edit.html', item=item,
                                  unique_items=unique_items, set_items=set_items,
                                  weapons=weapons, armors=armors, misc_items=misc_items,
                                  accounts=accounts, characters=characters, lang=lang)

@app.route('/my-items/delete/<int:item_id>')
@login_required
def my_items_delete(item_id):
    lang = request.args.get('lang', 'zh')
    user_id = session['user_id']
    db = get_db()

    # Check if item belongs to user before deleting
    item = query_db("SELECT id FROM my_items WHERE id = ? AND user_id = ?", (item_id, user_id), one=True)
    if not item:
        return jsonify({'error': 'Item not found'}), 404

    db.execute("DELETE FROM my_items WHERE id = ? AND user_id = ?", (item_id, user_id))
    db.commit()
    return f'<script>alert("删除成功!"); window.location.href="/my-items?lang={lang}";</script>'

# 'my_items.html' moved to templates/my_items.html

# 'my_items_add.html' moved to templates/my_items_add.html

# 'my_items_edit.html' moved to templates/my_items_edit.html

if __name__ == '__main__':
    debug = os.getenv('ENVIRONMENT') != 'production'
    app.run(
        debug=debug,
        host='127.0.0.1' if debug else '0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        use_reloader=debug
    )
