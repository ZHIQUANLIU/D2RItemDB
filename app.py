from flask import Flask, render_template_string, request, g, session, jsonify, send_from_directory, redirect, url_for
import sqlite3
import json
import os
import base64
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'd2r_item_db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SETTINGS_FILE'] = 'settings.json'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

DB_PATH = "d2r_items.db"

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def load_settings():
    if os.path.exists(app.config['SETTINGS_FILE']):
        with open(app.config['SETTINGS_FILE'], 'r') as f:
            return json.load(f)
    return {'gemini_api_key': '', 'ocr_method': 'easyocr'}

def save_settings(settings):
    with open(app.config['SETTINGS_FILE'], 'w') as f:
        json.dump(settings, f)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    lang = request.args.get('lang', 'zh')
    if request.method == 'POST':
        gemini_key = request.form.get('gemini_api_key', '').strip()
        ocr_method = request.form.get('ocr_method', 'gemini')
        save_settings({'gemini_api_key': gemini_key, 'ocr_method': ocr_method})
        return f'<script>alert("Settings saved!"); window.location.href="/?lang={lang}";</script>'
    
    s = load_settings()
    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Settings</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; background: #0a0a14; color: #ccc; padding: 40px; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        h1 {{ color: #f0c040; }}
        .form-group {{ margin-bottom: 20px; }}
        label {{ display: block; margin-bottom: 8px; color: #aaa; }}
        input, select {{ width: 100%; padding: 12px; background: #1a1a2a; color: #fff; border: 1px solid #333; border-radius: 6px; }}
        .btn {{ padding: 12px 24px; background: #f0c040; color: #000; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }}
        .btn-secondary {{ background: #4a4a5a; color: #fff; margin-left: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Settings</h1>
        <form method="post">
            <div class="form-group">
                <label>OCR Method</label>
                <select name="ocr_method">
                    <option value="gemini" {"selected" if s.get("ocr_method") == "gemini" else ""}>Google Gemini (AI - More Accurate)</option>
                    <option value="easyocr" {"selected" if s.get("ocr_method") == "easyocr" else ""}>EasyOCR (Local - Faster)</option>
                </select>
            </div>
            <div class="form-group">
                <label>Gemini API Key</label>
                <input type="text" name="gemini_api_key" value="{s.get('gemini_api_key', '')}" placeholder="Enter your Gemini API key">
                <div style="margin-top:8px;color:#666;font-size:12px;">Get API key from: https://aistudio.google.com/app/apikey</div>
            </div>
            <button type="submit" class="btn">Save</button>
            <a href="/" class="btn btn-secondary">Back</a>
            <a href="/accounts" class="btn btn-secondary" style="margin-left:10px;">Account Management</a>
        </form>
    </div>
</body>
</html>
'''

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
    
    return render_template_string(ACCOUNTS_TEMPLATE, accounts=accounts, characters=characters, lang=lang)

ACCOUNTS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{% if lang == 'zh' %}账户管理{% else %}Account Management{% endif %}</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0a0a14; color: #ccc; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { color: #f0c040; }
        .section { background: #1a1a30; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #aaa; }
        input, select { width: 100%; padding: 10px; background: #1a1a2a; color: #fff; border: 1px solid #333; border-radius: 4px; }
        .row { display: flex; gap: 10px; }
        .col { flex: 1; }
        .btn { padding: 10px 20px; background: #f0c040; color: #000; border: none; border-radius: 4px; cursor: pointer; }
        .btn-danger { background: #d44; color: #fff; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #333; }
        th { color: #f0c040; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{% if lang == 'zh' %}账户和角色管理{% else %}Account & Character Management{% endif %}</h1>
        
        <div class="section">
            <h2>{% if lang == 'zh' %}添加账户{% else %}Add Account{% endif %}</h2>
            <form method="post">
                <input type="hidden" name="action" value="add_account">
                <div class="row">
                    <div class="col">
                        <input type="text" name="account_name" placeholder="{% if lang == 'zh' %}账户名 (如 account#1){% else %}Account name (e.g. account#1){% endif %}" required>
                    </div>
                    <div class="col">
                        <input type="text" name="notes" placeholder="{% if lang == 'zh' %}备注{% else %}Notes{% endif %}">
                    </div>
                    <div class="col">
                        <button type="submit" class="btn">{% if lang == 'zh' %}添加账户{% else %}Add Account{% endif %}</button>
                    </div>
                </div>
            </form>
        </div>
        
        <div class="section">
            <h2>{% if lang == 'zh' %}账户列表{% else %}Accounts{% endif %}</h2>
            <table>
                <tr>
                    <th>{% if lang == 'zh' %}账户{% else %}Account{% endif %}</th>
                    <th>{% if lang == 'zh' %}备注{% else %}Notes{% endif %}</th>
                    <th>{% if lang == 'zh' %}角色{% else %}Characters{% endif %}</th>
                    <th>{% if lang == 'zh' %}操作{% else %}Actions{% endif %}</th>
                </tr>
                {% for acc in accounts %}
                <tr>
                    <td>{{ acc.name }}</td>
                    <td>{{ acc.notes or '' }}</td>
                    <td>
                        {% for char in characters %}
                            {% if char.account_id == acc.id %}
                                <span style="background:#2a2a40;padding:2px 8px;border-radius:3px;margin-right:5px;">
                                    {{ char.name }}{% if char.class %} ({{ char.class }}){% endif %}
                                    <form method="post" style="display:inline;">
                                        <input type="hidden" name="action" value="delete_character">
                                        <input type="hidden" name="char_id" value="{{ char.id }}">
                                        <button type="submit" style="background:none;border:none;color:#f44;cursor:pointer;padding:0;">×</button>
                                    </form>
                                </span>
                            {% endif %}
                        {% endfor %}
                    </td>
                    <td>
                        <form method="post" style="display:inline;">
                            <input type="hidden" name="action" value="add_character">
                            <input type="hidden" name="account_id" value="{{ acc.id }}">
                            <input type="text" name="char_name" placeholder="{% if lang == 'zh' %}角色名{% else %}Character{% endif %}" style="width:100px;display:inline;padding:5px;">
                            <select name="char_class" style="width:80px;display:inline;padding:5px;">
                                <option value="">-</option>
                                <option value="Amazon">Amazon</option>
                                <option value="Sorceress">Sorceress</option>
                                <option value="Necromancer">Necromancer</option>
                                <option value="Paladin">Paladin</option>
                                <option value="Barbarian">Barbarian</option>
                                <option value="Druid">Druid</option>
                                <option value="Assassin">Assassin</option>
                            </select>
                            <button type="submit" class="btn" style="padding:5px 10px;font-size:12px;">+</button>
                        </form>
                        <form method="post" style="display:inline;margin-left:10px;">
                            <input type="hidden" name="action" value="delete_account">
                            <input type="hidden" name="account_id" value="{{ acc.id }}">
                            <button type="submit" class="btn btn-danger" onclick="return confirm('{% if lang == 'zh' %}确定删除?{% else %}Confirm delete?{% endif %}')\">{% if lang == 'zh' %}删除{% else %}Delete{% endif %}</button>
                        </form>
                    </td>
                </tr>
                {% endfor %}
            </table>
        </div>
        
        <a href="/?lang={{ lang }}" class="btn">{% if lang == 'zh' %}返回{% else %}Back{% endif %}</a>
    </div>
</body>
</html>
'''

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
  "req_level": number,
  "req_str": number, 
  "req_dex": number,
  "defense": number,
  "enhanced_defense": number,
  "sockets": number,
  "durability": number,
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
  "absorb_fire": number,
  "absorb_cold": number,
  "absorb_ltng": number,
  "add_fire_min": number,
  "add_fire_max": number,
  "add_cold_min": number,
  "add_cold_max": number,
  "add_ltng_min": number,
  "add_ltng_max": number,
  "add_pois_min": number,
  "add_pois_max": number,
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
  "target_defense": number
}
If a stat is not present, use null.'''
    
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

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>D2R 物品查询 | Item Database</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a14; color: #ccc; min-height: 100vh; }
        .container { max-width: 1600px; margin: 0 auto; padding: 15px; }
        
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
        h1 { color: #f0c040; font-size: 1.6em; letter-spacing: 2px; }
        .lang-switch { display: flex; gap: 5px; }
        .lang-btn { padding: 6px 12px; background: #1a1a30; border: 1px solid #353550; border-radius: 4px; color: #666; cursor: pointer; font-size: 12px; }
        .lang-btn.active { background: #f0c040; color: #000; border-color: #f0c040; }
        
        .toolbar { background: linear-gradient(135deg, #151525 0%, #1a1a30 100%); padding: 15px; border-radius: 10px; margin-bottom: 15px; border: 1px solid #252540; }
        .toolbar-row { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 10px; }
        .toolbar-row:last-child { margin-bottom: 0; }
        
        .search-box { display: flex; flex: 1; gap: 8px; }
        .search-box input { flex: 1; padding: 10px 14px; font-size: 14px; border: 1px solid #353550; border-radius: 6px; background: #0a0a14; color: #ccc; }
        .search-box input:focus { outline: none; border-color: #f0c040; }
        .search-box button { padding: 10px 20px; font-size: 14px; background: linear-gradient(135deg, #e94560 0%, #c73e54 100%); color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; }
        
        .filter-group { display: flex; align-items: center; gap: 8px; }
        .filter-label { font-size: 12px; color: #666; }
        .filter-select { padding: 8px 12px; font-size: 13px; border: 1px solid #353550; border-radius: 6px; background: #0a0a14; color: #ccc; min-width: 100px; }
        
        .tabs { display: flex; gap: 6px; margin-bottom: 15px; flex-wrap: wrap; }
        .tab { padding: 8px 16px; background: #151525; border: 1px solid #252540; border-radius: 6px; color: #777; cursor: pointer; font-size: 13px; }
        .tab.active { background: #f0c040; color: #000; font-weight: 600; border-color: #f0c040; }
        .tab:hover:not(.active) { background: #252540; color: #aaa; }
        
        .results { display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); }
        
        .item-card { background: linear-gradient(145deg, #151525 0%, #10101c 100%); padding: 14px; border-radius: 8px; border-left: 3px solid #e94560; transition: all 0.2s; }
        .item-card:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,0,0,0.5); }
        .item-card.armor { border-left-color: #4a90d9; }
        .item-card.unique { border-left-color: #ffd700; }
        .item-card.set { border-left-color: #32cd32; }
        .item-card.misc { border-left-color: #9370db; }
        .item-card.gem { border-left-color: #ff69b4; }
        .item-card.rune { border-left-color: #00ced1; }
        
        .item-header { display: flex; align-items: flex-start; margin-bottom: 4px; }
        .item-icon { width: 28px; height: 28px; object-fit: contain; background: #1a1a2e; border-radius: 4px; margin-right: 8px; flex-shrink: 0; }
        .item-info { flex: 1; min-width: 0; }
        .item-name { font-size: 1.1em; color: #f0c040; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .item-name-en { font-size: 0.75em; color: #666; margin-top: 2px; }
        .item-code { font-size: 0.7em; color: #555; background: #0a0a14; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
        .item-type { color: #666; font-size: 0.8em; margin-bottom: 8px; }
        
        .item-stats { display: flex; flex-wrap: wrap; gap: 5px; margin: 8px 0; }
        .stat { display: inline-block; background: #1e1e30; padding: 3px 8px; border-radius: 4px; font-size: 0.75em; border: 1px solid #2a2a45; }
        .stat-label { color: #666; }
        .stat-value { color: #f0c040; font-weight: 600; }
        .damage { color: #e94560; }
        .defense { color: #4a90d9; }
        
        .item-props { color: #888; font-size: 0.8em; padding-top: 8px; border-top: 1px solid #252540; margin-top: 8px; }
        .prop { display: inline-block; background: #1a1a30; padding: 2px 6px; border-radius: 3px; margin: 2px; border: 1px solid #2a2a45; color: #a080c0; font-size: 0.75em; }
        .set-name { color: #32cd32; font-weight: 600; margin-top: 6px; font-size: 0.85em; }
        
        .raw-btn { padding: 5px 10px; font-size: 11px; background: #1e1e30; color: #666; border: 1px solid #2a2a45; border-radius: 4px; cursor: pointer; margin-top: 8px; }
        .raw-btn:hover { background: #2a2a45; color: #888; }
        
        .empty { text-align: center; color: #444; padding: 50px; font-size: 1.1em; }
        .count { color: #666; font-size: 0.85em; margin-bottom: 10px; }
        
        .pagination { display: flex; justify-content: center; gap: 5px; margin-top: 20px; flex-wrap: wrap; }
        .pagination a { padding: 8px 12px; background: #1a1a30; color: #888; text-decoration: none; border-radius: 4px; font-size: 13px; border: 1px solid #2a2a45; }
        .pagination a:hover { background: #2a2a45; color: #aaa; }
        .pagination a.active { background: #f0c040; color: #000; border-color: #f0c040; }
        
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); z-index: 1000; }
        .modal.show { display: flex; align-items: center; justify-content: center; }
        .modal-content { background: #151525; border-radius: 10px; max-width: 90%; max-height: 85%; width: 700px; border: 1px solid #353550; }
        .modal-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #252540; }
        .modal-title { font-size: 1.1em; color: #f0c040; }
        .modal-close { background: none; border: none; color: #666; font-size: 20px; cursor: pointer; }
        .modal-close:hover { color: #e94560; }
        .modal-body { padding: 16px; max-height: 65vh; overflow: auto; }
        .modal-body pre { background: #0a0a14; padding: 12px; border-radius: 6px; font-size: 11px; color: #888; overflow-x: auto; white-space: pre-wrap; word-break: break-all; line-height: 1.6; }
        .modal-body .json-key { color: #6a9fd4; }
        .modal-body .json-string { color: #7ec699; }
        .modal-body .json-number { color: #e8a85c; }
        .modal-body .json-section { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #2a2a45; }
        .modal-body .json-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }
        .modal-body .section-title { color: #f0c040; font-size: 12px; margin-bottom: 8px; font-weight: 600; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚔️ D2R 物品查询 | Item Database</h1>
            <div style="display:flex;gap:10px;align-items:center;">
                <a href="/settings?lang={{ lang }}" style="color:#888;text-decoration:none;padding:5px 10px;background:#1a1a30;border-radius:4px;font-size:13px;">{% if lang == 'zh' %}设置{% else %}Settings{% endif %}</a>
                <a href="/my-items?lang={{ lang }}" style="color:#f0c040;text-decoration:none;padding:5px 10px;background:#1a1a30;border-radius:4px;font-size:13px;">{% if lang == 'zh' %}我的物品{% else %}My Items{% endif %}</a>
                <div class="lang-switch">
                    <button class="lang-btn {% if lang=='zh' %}active{% endif %}" onclick="setLang('zh')">中文</button>
                    <button class="lang-btn {% if lang=='en' %}active{% endif %}" onclick="setLang('en')">English</button>
                </div>
            </div>
        </div>
        
        <div class="toolbar">
            <div class="toolbar-row">
                <form method="get" class="search-box">
                    <input type="text" name="q" placeholder="{{ '搜索物品名称...' if lang=='zh' else 'Search items...' }}" value="{{ request.args.get('q', '') }}">
                    <input type="hidden" name="lang" value="{{ lang }}">
                    <button type="submit">{{ '搜索' if lang=='zh' else 'Search' }}</button>
                </form>
            </div>
            <div class="toolbar-row">
                <div class="filter-group">
                    <span class="filter-label">{{ '分类' if lang=='zh' else 'Category' }}:</span>
                    <select class="filter-select" onchange="location.href=this.value">
                        <option value="?{{ build_query('category', 'all') }}" {% if not request.args.get('category') or request.args.get('category')=='all' %}selected{% endif %}>{{ '全部' if lang=='zh' else 'All' }}</option>
                        <option value="?{{ build_query('category', 'weapons') }}" {% if request.args.get('category')=='weapons' %}selected{% endif %}>{{ '武器' if lang=='zh' else 'Weapons' }}</option>
                        <option value="?{{ build_query('category', 'armor') }}" {% if request.args.get('category')=='armor' %}selected{% endif %}>{{ '护甲' if lang=='zh' else 'Armor' }}</option>
                        <option value="?{{ build_query('category', 'unique') }}" {% if request.args.get('category')=='unique' %}selected{% endif %}>{{ '暗金' if lang=='zh' else 'Unique' }}</option>
                        <option value="?{{ build_query('category', 'set') }}" {% if request.args.get('category')=='set' %}selected{% endif %}>{{ '套装' if lang=='zh' else 'Set' }}</option>
                        <option value="?{{ build_query('category', 'misc') }}" {% if request.args.get('category')=='misc' %}selected{% endif %}>{{ '杂物' if lang=='zh' else 'Misc' }}</option>
                        <option value="?{{ build_query('category', 'gems') }}" {% if request.args.get('category')=='gems' %}selected{% endif %}>{{ '宝石' if lang=='zh' else 'Gems' }}</option>
                        <option value="?{{ build_query('category', 'runes') }}" {% if request.args.get('category')=='runes' %}selected{% endif %}>{{ '符文' if lang=='zh' else 'Runes' }}</option>
                    </select>
                </div>
                
                {% if request.args.get('category') == 'weapons' %}
                <div class="filter-group">
                    <span class="filter-label">{{ '武器类型' if lang=='zh' else 'Weapon Type' }}:</span>
                    <select class="filter-select" onchange="location.href=this.value">
                        <option value="?{{ build_query('wtype', 'all') }}" {% if not request.args.get('wtype') or request.args.get('wtype')=='all' %}selected{% endif %}>{{ '全部' if lang=='zh' else 'All' }}</option>
                        <option value="?{{ build_query('wtype', 'axe') }}" {% if request.args.get('wtype')=='axe' %}selected{% endif %}>{{ '斧子' if lang=='zh' else 'Axe' }}</option>
                        <option value="?{{ build_query('wtype', 'sword') }}" {% if request.args.get('wtype')=='sword' %}selected{% endif %}>{{ '剑' if lang=='zh' else 'Sword' }}</option>
                        <option value="?{{ build_query('wtype', 'bow') }}" {% if request.args.get('wtype')=='bow' %}selected{% endif %}>{{ '弓' if lang=='zh' else 'Bow' }}</option>
                        <option value="?{{ build_query('wtype', 'crossbow') }}" {% if request.args.get('wtype')=='crossbow' %}selected{% endif %}>{{ '弩' if lang=='zh' else 'Crossbow' }}</option>
                        <option value="?{{ build_query('wtype', 'mace') }}" {% if request.args.get('wtype')=='mace' %}selected{% endif %}>{{ '锤' if lang=='zh' else 'Mace' }}</option>
                        <option value="?{{ build_query('wtype', 'staff') }}" {% if request.args.get('wtype')=='staff' %}selected{% endif %}>{{ '法杖' if lang=='zh' else 'Staff' }}</option>
                        <option value="?{{ build_query('wtype', 'wand') }}" {% if request.args.get('wtype')=='wand' %}selected{% endif %}>{{ '魔杖' if lang=='zh' else 'Wand' }}</option>
                        <option value="?{{ build_query('wtype', 'scepter') }}" {% if request.args.get('wtype')=='scepter' %}selected{% endif %}>{{ '权杖' if lang=='zh' else 'Scepter' }}</option>
                        <option value="?{{ build_query('wtype', 'spear') }}" {% if request.args.get('wtype')=='spear' %}selected{% endif %}>{{ '矛' if lang=='zh' else 'Spear' }}</option>
                        <option value="?{{ build_query('wtype', 'polearm') }}" {% if request.args.get('wtype')=='polearm' %}selected{% endif %}>{{ '长柄' if lang=='zh' else 'Polearm' }}</option>
                        <option value="?{{ build_query('wtype', 'dagger') }}" {% if request.args.get('wtype')=='dagger' %}selected{% endif %}>{{ '匕首' if lang=='zh' else 'Dagger' }}</option>
                        <option value="?{{ build_query('wtype', 'javelin') }}" {% if request.args.get('wtype')=='javelin' %}selected{% endif %}>{{ '标枪' if lang=='zh' else 'Javelin' }}</option>
                    </select>
                </div>
                {% endif %}
                
                {% if request.args.get('category') == 'armor' %}
                <div class="filter-group">
                    <span class="filter-label">{{ '护甲类型' if lang=='zh' else 'Armor Type' }}:</span>
                    <select class="filter-select" onchange="location.href=this.value">
                        <option value="?{{ build_query('atype', 'all') }}" {% if not request.args.get('atype') or request.args.get('atype')=='all' %}selected{% endif %}>{{ '全部' if lang=='zh' else 'All' }}</option>
                        <option value="?{{ build_query('atype', 'tors') }}" {% if request.args.get('atype')=='tors' %}selected{% endif %}>{{ '衣服' if lang=='zh' else 'Armor' }}</option>
                        <option value="?{{ build_query('atype', 'helm') }}" {% if request.args.get('atype')=='helm' %}selected{% endif %}>{{ '头盔' if lang=='zh' else 'Helm' }}</option>
                        <option value="?{{ build_query('atype', 'shie') }}" {% if request.args.get('atype')=='shie' %}selected{% endif %}>{{ '盾牌' if lang=='zh' else 'Shield' }}</option>
                        <option value="?{{ build_query('atype', 'belt') }}" {% if request.args.get('atype')=='belt' %}selected{% endif %}>{{ '腰带' if lang=='zh' else 'Belt' }}</option>
                        <option value="?{{ build_query('atype', 'glov') }}" {% if request.args.get('atype')=='glov' %}selected{% endif %}>{{ '手套' if lang=='zh' else 'Gloves' }}</option>
                        <option value="?{{ build_query('atype', 'boot') }}" {% if request.args.get('atype')=='boot' %}selected{% endif %}>{{ '靴子' if lang=='zh' else 'Boots' }}</option>
                    </select>
                </div>
                {% endif %}
                
                <div class="filter-group">
                    <span class="filter-label">{{ '每页' if lang=='zh' else 'Per page' }}:</span>
                    <select class="filter-select" onchange="location.href=this.value">
                        <option value="?{{ build_query('per_page', 25) }}" {% if per_page==25 %}selected{% endif %}>25</option>
                        <option value="?{{ build_query('per_page', 50) }}" {% if per_page==50 %}selected{% endif %}>50</option>
                        <option value="?{{ build_query('per_page', 100) }}" {% if per_page==100 %}selected{% endif %}>100</option>
                        <option value="?{{ build_query('per_page', 200) }}" {% if per_page==200 %}selected{% endif %}>200</option>
                    </select>
                </div>
                
                <div class="sort-group">
                    <span class="filter-label">{{ '排序' if lang=='zh' else 'Sort' }}:</span>
                    <select class="filter-select" onchange="location.href=this.value">
                        <option value="?{{ build_query('sort', 'level') }}" {% if not request.args.get('sort') or request.args.get('sort')=='level' %}selected{% endif %}>{{ '等级↑' if lang=='zh' else 'Level ↑' }}</option>
                        <option value="?{{ build_query('sort', 'level_desc') }}" {% if request.args.get('sort')=='level_desc' %}selected{% endif %}>{{ '等级↓' if lang=='zh' else 'Level ↓' }}</option>
                        <option value="?{{ build_query('sort', 'damage') }}" {% if request.args.get('sort')=='damage' %}selected{% endif %}>{{ '伤害↑' if lang=='zh' else 'Damage ↑' }}</option>
                        <option value="?{{ build_query('sort', 'damage_desc') }}" {% if request.args.get('sort')=='damage_desc' %}selected{% endif %}>{{ '伤害↓' if lang=='zh' else 'Damage ↓' }}</option>
                        <option value="?{{ build_query('sort', 'defense') }}" {% if request.args.get('sort')=='defense' %}selected{% endif %}>{{ '防御↑' if lang=='zh' else 'Defense ↑' }}</option>
                        <option value="?{{ build_query('sort', 'defense_desc') }}" {% if request.args.get('sort')=='defense_desc' %}selected{% endif %}>{{ '防御↓' if lang=='zh' else 'Defense ↓' }}</option>
                        <option value="?{{ build_query('sort', 'cost') }}" {% if request.args.get('sort')=='cost' %}selected{% endif %}>{{ '价格↑' if lang=='zh' else 'Price ↑' }}</option>
                        <option value="?{{ build_query('sort', 'cost_desc') }}" {% if request.args.get('sort')=='cost_desc' %}selected{% endif %}>{{ '价格↓' if lang=='zh' else 'Price ↓' }}</option>
                        <option value="?{{ build_query('sort', 'name') }}" {% if request.args.get('sort')=='name' %}selected{% endif %}>{{ '名称' if lang=='zh' else 'Name' }}</option>
                    </select>
                </div>
            </div>
        </div>
        
        <div class="tabs">
            <a href="?{{ build_query('category', 'all') }}" class="tab {% if not request.args.get('category') or request.args.get('category')=='all' %}active{% endif %}">{{ '全部' if lang=='zh' else 'All' }}</a>
            <a href="?{{ build_query('category', 'weapons') }}" class="tab {% if request.args.get('category')=='weapons' %}active{% endif %}">{{ '武器' if lang=='zh' else 'Weapons' }}</a>
            <a href="?{{ build_query('category', 'armor') }}" class="tab {% if request.args.get('category')=='armor' %}active{% endif %}">{{ '护甲' if lang=='zh' else 'Armor' }}</a>
            <a href="?{{ build_query('category', 'unique') }}" class="tab {% if request.args.get('category')=='unique' %}active{% endif %}">{{ '暗金' if lang=='zh' else 'Unique' }}</a>
            <a href="?{{ build_query('category', 'set') }}" class="tab {% if request.args.get('category')=='set' %}active{% endif %}">{{ '套装' if lang=='zh' else 'Set' }}</a>
            <a href="?{{ build_query('category', 'misc') }}" class="tab {% if request.args.get('category')=='misc' %}active{% endif %}">{{ '杂物' if lang=='zh' else 'Misc' }}</a>
            <a href="?{{ build_query('category', 'gems') }}" class="tab {% if request.args.get('category')=='gems' %}active{% endif %}">{{ '宝石' if lang=='zh' else 'Gems' }}</a>
            <a href="?{{ build_query('category', 'runes') }}" class="tab {% if request.args.get('category')=='runes' %}active{% endif %}">{{ '符文' if lang=='zh' else 'Runes' }}</a>
        </div>
        
        <div class="count">
            {{ ('共 %d 件物品，第 %d/%d 页' if lang=='zh' else 'Total %d items, Page %d/%d')|format(total_count, page, total_pages) }}
        </div>
        
        <div class="results">
            {% if items %}
                {% for item in items %}
                <div class="item-card {{ item.category }}">
                    <div class="item-header">
                        {% if item.image_url %}
                        <img src="{{ item.image_url }}" class="item-icon" onerror="this.style.display='none'">
                        {% endif %}
                        <div class="item-info">
                            <div class="item-name">
                                {% if item.unique_name is defined and item.unique_name %}{{ item.unique_name }}
                                {% elif item.set_item_name is defined and item.set_item_name %}{{ item.set_item_name }}
                                {% else %}{{ item.name }}{% endif %}
                            </div>
                            {% if item.base_name is defined and item.base_name and item.name is defined and item.base_name != item.name and ((item.unique_name is defined and item.unique_name) or (item.set_item_name is defined and item.set_item_name)) %}
                            <div class="item-name-en">{{ item.base_name }}</div>
                            {% endif %}
                        </div>
                        <div class="item-code">{{ item.code }}</div>
                    </div>
                    <div class="item-type">{{ translate_type(item.type, lang) }}</div>
                    
                    {% if item.mindam is defined or item.minac is defined %}
                    <div class="item-stats">
                        {% if item.mindam is defined and item.maxdam is defined %}
                            {% if item.mindam or item.maxdam %}
                            <span class="stat damage">{{ '伤害' if lang=='zh' else 'Damage' }}: <span class="stat-value">{{ item.mindam }}-{{ item.maxdam }}</span></span>
                            {% endif %}
                        {% endif %}
                        {% if item.minac is defined and item.maxac is defined %}
                            {% if item.minac or item.maxac %}
                            <span class="stat defense">{{ '防御' if lang=='zh' else 'Defense' }}: <span class="stat-value">{{ item.minac }}-{{ item.maxac }}</span></span>
                            {% endif %}
                        {% endif %}
                    </div>
                    {% endif %}
                    
                    <div class="item-stats">
                        {% if item.level %} <span class="stat"><span class="stat-label">{{ '等级' if lang=='zh' else 'Level' }}</span> <span class="stat-value">{{ item.level }}</span></span>{% endif %}
                        {% if item.levelreq %} <span class="stat"><span class="stat-label">{{ '需求' if lang=='zh' else 'Req' }}</span> <span class="stat-value">{{ item.levelreq }}</span></span>{% endif %}
                        {% if item.speed is defined and item.speed != 0 %} <span class="stat"><span class="stat-label">{{ '速度' if lang=='zh' else 'Speed' }}</span> <span class="stat-value">{{ item.speed }}</span></span>{% endif %}
                        {% if item.reqstr %} <span class="stat"><span class="stat-label">{{ '力量' if lang=='zh' else 'Str' }}</span> <span class="stat-value">{{ item.reqstr }}</span></span>{% endif %}
                        {% if item.reqdex %} <span class="stat"><span class="stat-label">{{ '敏捷' if lang=='zh' else 'Dex' }}</span> <span class="stat-value">{{ item.reqdex }}</span></span>{% endif %}
                        {% if item.durability and item.durability > 0 %} <span class="stat"><span class="stat-label">{{ '耐久' if lang=='zh' else 'Dur' }}</span> <span class="stat-value">{{ item.durability }}</span></span>{% endif %}
                        {% if item.sockets %} <span class="stat"><span class="stat-label">{{ '孔' if lang=='zh' else 'Sockets' }}</span> <span class="stat-value">{{ item.sockets }}</span></span>{% endif %}
                        {% if item.cost %} <span class="stat"><span class="stat-label">{{ '价格' if lang=='zh' else 'Price' }}</span> <span class="stat-value">{{ item.cost }}</span></span>{% endif %}
                    </div>
                    
                    {% if item.props %}
                    <div class="item-props">
                        {% for prop in item.props.split(',') %}
                        <span class="prop">{{ translate_prop(prop.strip(), lang) }}</span>
                        {% endfor %}
                    </div>
                    {% endif %}
                    
                    {% if item.full_set_name %}
                    <div class="set-name">{{ '套装' if lang=='zh' else 'Set' }}: {{ item.full_set_name }}</div>
                    {% endif %}
                    
                    {% if item.rune1 %}
                    <div class="item-stats">
                        <span class="stat"><span class="stat-label">{{ '符文' if lang=='zh' else 'Rune' }}</span> <span class="stat-value">{{ item.rune1 }} {{ item.rune2 }} {{ item.rune3 }}</span></span>
                    </div>
                    {% endif %}
                    
                    <button class="raw-btn" onclick="showModal('{{ (item.unique_name or item.set_item_name or item.name)|replace(\"'\", \"\\\\'\") }}', '{{ item.raw_data|replace('\\n',' ')|replace('\"','&quot;')|safe }}')">{{ '原始数据' if lang=='zh' else 'Raw Data' }}</button>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty">{{ '未找到物品' if lang=='zh' else 'No items found' }}</div>
            {% endif %}
        </div>
        
        {% if total_pages > 1 %}
        <div class="pagination">
            {% if page > 1 %}
            <a href="?{{ build_query('page', 1) }}">{{ '<<' if lang=='zh' else '<<' }}</a>
            <a href="?{{ build_query('page', page-1) }}">{{ '<' if lang=='zh' else '<' }}</a>
            {% endif %}
            
            {% for p in range([1, page-2]|max, [total_pages, page+3]|min+1) %}
            <a href="?{{ build_query('page', p) }}" {% if p==page %}class="active"{% endif %}>{{ p }}</a>
            {% endfor %}
            
            {% if page < total_pages %}
            <a href="?{{ build_query('page', page+1) }}">{{ '>' if lang=='zh' else '>' }}</a>
            <a href="?{{ build_query('page', total_pages) }}">{{ '>>' if lang=='zh' else '>>' }}</a>
            {% endif %}
        </div>
        {% endif %}
    </div>
    
    <div class="modal" id="dataModal" onclick="if(event.target===this)closeModal()">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title" id="modalTitle"></div>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <pre id="modalBody"></pre>
            </div>
        </div>
    </div>
    
    <script>
    function setLang(lang) {
        var url = new URL(window.location);
        url.searchParams.set('lang', lang);
        window.location.href = url.toString();
    }
    var currentLang = new URLSearchParams(window.location.search).get('lang') || 'zh';
    
    function formatJson(data) {
        try {
            const obj = JSON.parse(data.replace(/&quot;/g, '"'));
            const keys = Object.keys(obj);
            
            const important = ['name', 'code', 'type', 'level', 'lvl', 'levelreq', 'mindam', 'maxdam', 'minac', 'maxac', 'speed', 'cost', 'durability', 'sockets', 'reqstr', 'reqdex'];
            const importantKeys = keys.filter(k => important.includes(k.toLowerCase()));
            const otherKeys = keys.filter(k => !important.includes(k.toLowerCase()));
            
            let html = '';
            let title1 = currentLang === 'zh' ? '基础属性' : 'Basic Properties';
            let title2 = currentLang === 'zh' ? '其他属性' : 'Other Fields';
            let moreText = currentLang === 'zh' ? '...还有 ' : '... and ';
            let fieldsText = currentLang === 'zh' ? ' 个字段' : ' more fields';
            
            if (importantKeys.length > 0) {
                html += '<div class=\"json-section\"><div class=\"section-title\">' + title1 + '</div>';
                importantKeys.forEach(k => {
                    html += '<span class=\"json-key\">' + k + '</span>: <span class=\"json-number\">' + obj[k] + '</span> ';
                });
                html += '</div>';
            }
            
            if (otherKeys.length > 0) {
                html += '<div class=\"json-section\"><div class=\"section-title\">' + title2 + '</div>';
                otherKeys.slice(0, 30).forEach(k => {
                    let val = obj[k];
                    if (String(val).length > 30) val = String(val).substring(0, 30) + '...';
                    html += '<span class=\"json-key\">' + k + '</span>: <span class=\"json-string\">' + val + '</span> ';
                });
                if (otherKeys.length > 30) {
                    html += '<br><span style=\"color:#666\">' + moreText + (otherKeys.length - 30) + fieldsText + '</span>';
                }
                html += '</div>';
            }
            
            return html;
        } catch(e) {
            return '<pre>' + data + '</pre>';
        }
    }
    
    function showModal(title, data) {
        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalBody').innerHTML = formatJson(data);
        document.getElementById('dataModal').classList.add('show');
    }
    function closeModal() {
        document.getElementById('dataModal').classList.remove('show');
    }
    document.addEventListener('keydown', function(e) {
        if(e.key === 'Escape') closeModal();
    });
    </script>
</body>
</html>
'''

def build_query(key, value):
    args = request.args.copy()
    args[key] = value
    return '&'.join(f'{k}={v}' for k, v in args.items())

@app.context_processor
def inject_helpers():
    return dict(build_query=build_query, translate_type=translate_item_type, translate_prop=translate_prop, 
                min=min, max=max, range=range)

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')
    wtype = request.args.get('wtype', 'all')
    atype = request.args.get('atype', 'all')
    sort = request.args.get('sort', 'level')
    lang = request.args.get('lang', 'zh')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    items = []
    total_count = 0
    
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
    
    where_q = f"AND name LIKE '%{q}%'" if q else ""
    offset = (page - 1) * per_page
    
    total_count = 0
    
    if category in ('all', 'weapons'):
        wtype_where = ""
        if wtype != 'all' and wtype in wtype_map:
            types = "','".join(wtype_map[wtype])
            wtype_where = f"AND type IN ('{types}')"
        
        order = get_sort_order(sort, 'weapons')
        sql = f"SELECT *, 'weapons' as category FROM weapons WHERE 1=1 {where_q} {wtype_where} ORDER BY {order} LIMIT {per_page} OFFSET {offset}"
        rows = query_db(sql)
        items.extend([row_to_dict(r) for r in rows])
        
        cnt_sql = f"SELECT COUNT(*) FROM weapons WHERE 1=1 {where_q} {wtype_where}"
        cnt = query_db(cnt_sql, one=True)
        total_count += cnt[0] if cnt else 0
    
    if category in ('all', 'armor'):
        atype_where = ""
        if atype != 'all':
            atype_where = f"AND type = '{atype}'"
        
        order = get_sort_order(sort, 'armor')
        sql = f"SELECT *, 'armor' as category FROM armor WHERE 1=1 {where_q} {atype_where} ORDER BY {order} LIMIT {per_page} OFFSET {offset}"
        rows = query_db(sql)
        items.extend([row_to_dict(r) for r in rows])
        
        cnt_sql = f"SELECT COUNT(*) FROM armor WHERE 1=1 {where_q} {atype_where}"
        cnt = query_db(cnt_sql, one=True)
        total_count += cnt[0] if cnt else 0
    
    if category in ('all', 'unique'):
        order = get_sort_order(sort, 'unique')
        unique_where = f"AND (name LIKE '%{q}%' OR index_name LIKE '%{q}%')" if q else ""
        sql = f"SELECT index_name as unique_name, name as base_name, code, level, levelreq, rarity, cost_mult, cost_add, props, raw_data, 'unique' as category FROM unique_items WHERE 1=1 {unique_where} ORDER BY {order} LIMIT {per_page} OFFSET {offset}"
        rows = query_db(sql)
        items.extend([row_to_dict(r) for r in rows])
        
        cnt_sql = f"SELECT COUNT(*) FROM unique_items WHERE 1=1 {unique_where}"
        cnt = query_db(cnt_sql, one=True)
        total_count += cnt[0] if cnt else 0
    
    if category in ('all', 'set'):
        order = get_sort_order(sort, 'set')
        set_where = f"AND (name LIKE '%{q}%' OR index_name LIKE '%{q}%' OR set_name LIKE '%{q}%')" if q else ""
        sql = f"SELECT index_name as set_item_name, name as base_name, code, set_name as full_set_name, level, levelreq, rarity, cost_mult, props, raw_data, 'set' as category FROM set_items WHERE 1=1 {set_where} ORDER BY {order} LIMIT {per_page} OFFSET {offset}"
        rows = query_db(sql)
        items.extend([row_to_dict(r) for r in rows])
        
        cnt_sql = f"SELECT COUNT(*) FROM set_items WHERE 1=1 {set_where}"
        cnt = query_db(cnt_sql, one=True)
        total_count += cnt[0] if cnt else 0
    
    if category in ('all', 'misc'):
        order = get_sort_order(sort, 'misc')
        sql = f"SELECT *, 'misc' as category FROM misc WHERE 1=1 {where_q} ORDER BY {order} LIMIT {per_page} OFFSET {offset}"
        rows = query_db(sql)
        items.extend([row_to_dict(r) for r in rows])
        
        cnt_sql = f"SELECT COUNT(*) FROM misc WHERE 1=1 {where_q}"
        cnt = query_db(cnt_sql, one=True)
        total_count += cnt[0] if cnt else 0
    
    if category in ('all', 'gems'):
        order = get_sort_order(sort, 'gems')
        sql = f"SELECT *, 'gem' as category FROM gems WHERE 1=1 {where_q} ORDER BY {order} LIMIT {per_page} OFFSET {offset}"
        rows = query_db(sql)
        items.extend([row_to_dict(r) for r in rows])
        
        cnt_sql = f"SELECT COUNT(*) FROM gems WHERE 1=1 {where_q}"
        cnt = query_db(cnt_sql, one=True)
        total_count += cnt[0] if cnt else 0
    
    if category in ('all', 'runes'):
        order = get_sort_order(sort, 'runes')
        sql = f"SELECT *, 'rune' as category FROM runes WHERE 1=1 {where_q} ORDER BY {order} LIMIT {per_page} OFFSET {offset}"
        rows = query_db(sql)
        items.extend([row_to_dict(r) for r in rows])
        
        cnt_sql = f"SELECT COUNT(*) FROM runes WHERE 1=1 {where_q}"
        cnt = query_db(cnt_sql, one=True)
        total_count += cnt[0] if cnt else 0
    
    # Calculate pagination
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
    
    return render_template_string(HTML_TEMPLATE, items=items, request=request, lang=lang, 
                                   page=page, total_pages=total_pages, total_count=total_count, per_page=per_page)

# 我的物品管理路由
@app.route('/my-items')
def my_items():
    lang = request.args.get('lang', 'zh')
    account = request.args.get('account', '')
    storage_type = request.args.get('storage_type', '')
    
    where = "1=1"
    if account:
        where += f" AND account LIKE '%{account}%'"
    if storage_type:
        where += f" AND storage_type = '{storage_type}'"
    
    sql = f"SELECT * FROM my_items WHERE {where} ORDER BY create_time DESC"
    items = query_db(sql)
    
    accounts_sql = "SELECT DISTINCT account FROM my_items ORDER BY account"
    accounts = [r[0] for r in query_db(accounts_sql)]
    
    return render_template_string(MY_ITEMS_TEMPLATE, items=items, accounts=accounts, 
                                selected_account=account, selected_storage=storage_type, lang=lang)

@app.route('/my-items/add', methods=['GET', 'POST'])
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
        cols = "item_type, item_id, account, character_name, storage_type, storage_name, notes, image_path, is_ethereal, is_artifact, sockets, req_level, req_str, req_dex, defense, enhanced_defense, durability, damage_min, damage_max, str_bonus, dex_bonus, vit_bonus, ene_bonus, life, mana, skill_name, skill_level, ctc_trigger, ctc_skill_name, ctc_skill_level, ias, fcr, fhr, frw, res_fire, res_cold, res_ltng, res_pois, res_all, absorb_fire, absorb_cold, absorb_ltng, add_fire_min, add_fire_max, add_cold_min, add_cold_max, add_ltng_min, add_ltng_max, add_pois_min, add_pois_max, mf, eg, life_steal, mana_steal, life_after_kill, mana_after_kill, attack_rating, attack_rating_plus, crushing_blow, deadly_strike, open_wounds, cannot_be_frozen, ctc_trigger2, ctc_skill_name2, ctc_skill_level2, ctc_trigger3, ctc_skill_name3, ctc_skill_level3"
        vals = (item_type, item_id, account, character_name, storage_type, storage_name, notes, image_path, is_ethereal, is_artifact, sockets, req_level, req_str, req_dex, defense, enhanced_defense, durability, damage_min, damage_max, str_bonus, dex_bonus, vit_bonus, ene_bonus, life, mana, skill_name, skill_level, ctc_trigger, ctc_skill_name, ctc_skill_level, ias, fcr, fhr, frw, res_fire, res_cold, res_ltng, res_pois, res_all, absorb_fire, absorb_cold, absorb_ltng, add_fire_min, add_fire_max, add_cold_min, add_cold_max, add_ltng_min, add_ltng_max, add_pois_min, add_pois_max, mf_val, eg, life_steal, mana_steal, life_after_kill, mana_after_kill, attack_rating, attack_rating_plus, crushing_blow, deadly_strike, open_wounds, cannot_be_frozen, ctc_trigger2, ctc_skill_name2, ctc_skill_level2, ctc_trigger3, ctc_skill_name3, ctc_skill_level3)
        placeholders = '(' + ', '.join(['?'] * len(vals)) + ')'
        db.execute(f'INSERT INTO my_items ({cols}) VALUES {placeholders}', vals)
        db.commit()
        return f'<script>alert("添加成功!"); window.location.href="/my-items?lang={lang}";</script>'
    
    unique_items = [tuple(r) for r in query_db("SELECT index_name, name FROM unique_items ORDER BY index_name")]
    set_items = [tuple(r) for r in query_db("SELECT index_name, set_name FROM set_items ORDER BY index_name")]
    weapons = [tuple(r) for r in query_db("SELECT name, type FROM weapons ORDER BY name")]
    armors = [tuple(r) for r in query_db("SELECT name, type FROM armor ORDER BY name")]
    misc_items = [tuple(r) for r in query_db("SELECT name, type FROM misc ORDER BY name")]
    accounts = [tuple(r) for r in query_db("SELECT id, name FROM accounts ORDER BY name")]
    characters = [tuple(r) for r in query_db("SELECT id, account_id, name, class FROM characters ORDER BY name")]
    
    return render_template_string(MY_ITEMS_ADD_TEMPLATE, 
                                  unique_items=unique_items, 
                                  set_items=set_items,
                                  weapons=weapons,
                                  armors=armors,
                                  misc_items=misc_items,
                                  accounts=accounts,
                                  characters=characters,
                                  lang=lang)

@app.route('/my-items/edit/<int:item_id>', methods=['GET', 'POST'])
def my_items_edit(item_id):
    lang = request.args.get('lang', 'zh')
    db = get_db()
    
    if request.method == 'POST':
        item_type = request.form.get('item_type', 'normal')
        item_id = request.form.get('item_id', '')
        account = request.form.get('account', '')
        character_name = request.form.get('character_name', '')
        storage_type = request.form.get('storage_type', '')
        storage_name = request.form.get('storage_name', '')
        notes = request.form.get('notes', '')
        is_ethereal = 1 if request.form.get('is_ethereal') else 0
        is_artifact = 1 if request.form.get('is_artifact') else 0
        quality = int(request.form.get('quality', 0))
        defense = int(request.form.get('defense', 0)) or None
        enhanced_damage = int(request.form.get('enhanced_damage', 0)) or None
        skills = int(request.form.get('skills', 0)) or None
        all_resists = int(request.form.get('all_resists', 0)) or None
        mf = int(request.form.get('mf', 0)) or None
        sockets = int(request.form.get('sockets', 0)) or None
        
        db.execute('''
            UPDATE my_items SET item_type=?, item_id=?, account=?, character_name=?, storage_type=?, storage_name=?, notes=?, is_ethereal=?, is_artifact=?, quality=?, defense=?, enhanced_damage=?, skills=?, all_resists=?, mf=?, sockets=?, update_time=CURRENT_TIMESTAMP
            WHERE id=?
        ''', (item_type, item_id, account, character_name, storage_type, storage_name, notes, is_ethereal, is_artifact, quality, defense, enhanced_damage, skills, all_resists, mf, sockets, item_id))
        db.commit()
        return f'<script>alert("更新成功!"); window.location.href="/my-items?lang={lang}";</script>'
    
    item = query_db("SELECT * FROM my_items WHERE id = ?", (item_id,), one=True)
    unique_items = [tuple(r) for r in query_db("SELECT index_name, name FROM unique_items ORDER BY index_name")]
    set_items = [tuple(r) for r in query_db("SELECT index_name, set_name FROM set_items ORDER BY index_name")]
    weapons = [tuple(r) for r in query_db("SELECT name, type FROM weapons ORDER BY name")]
    armors = [tuple(r) for r in query_db("SELECT name, type FROM armor ORDER BY name")]
    misc_items = [tuple(r) for r in query_db("SELECT name, type FROM misc ORDER BY name")]
    accounts = [tuple(r) for r in query_db("SELECT id, name FROM accounts ORDER BY name")]
    characters = [tuple(r) for r in query_db("SELECT id, account_id, name, class FROM characters ORDER BY name")]
    
    return render_template_string(MY_ITEMS_EDIT_TEMPLATE, item=item, 
                                  unique_items=unique_items, set_items=set_items,
                                  weapons=weapons, armors=armors, misc_items=misc_items,
                                  accounts=accounts, characters=characters, lang=lang)

@app.route('/my-items/delete/<int:item_id>')
def my_items_delete(item_id):
    lang = request.args.get('lang', 'zh')
    db = get_db()
    db.execute("DELETE FROM my_items WHERE id = ?", (item_id,))
    db.commit()
    return f'<script>alert("删除成功!"); window.location.href="/my-items?lang={lang}";</script>'

MY_ITEMS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>我的物品 | My Items</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a14; color: #ccc; min-height: 100vh; }
        .container { max-width: 1400px; margin: 0 auto; padding: 15px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        h1 { color: #f0c040; font-size: 1.6em; }
        .btn { padding: 8px 16px; background: #4a4a5a; color: #fff; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; }
        .btn-primary { background: #f0c040; color: #000; }
        .btn-danger { background: #d44; }
        .btn:hover { opacity: 0.8; }
        .filter-bar { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        select, input { padding: 8px; background: #1a1a2a; color: #ccc; border: 1px solid #333; border-radius: 4px; }
        table { width: 100%; border-collapse: collapse; background: #12121a; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #333; }
        th { background: #1a1a2a; color: #f0c040; }
        tr:hover { background: #1a1a2a; }
        .eth { color: #a0a; }
        .perfect { color: #0f0; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; }
        .badge-stash { background: #338; }
        .badge-char { background: #383; }
        .badge-shared { background: #833; }
        .empty { text-align: center; padding: 40px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{% if lang == 'zh' %}我的物品{% else %}My Items{% endif %}</h1>
            <div>
                <a href="/my-items/add?lang={{ lang }}" class="btn btn-primary">{% if lang == 'zh' %}添加物品{% else %}Add Item{% endif %}</a>
                <a href="/?lang={{ lang }}" class="btn">{% if lang == 'zh' %}返回{% else %}Back{% endif %}</a>
            </div>
        </div>
        
        <div class="filter-bar">
            <form method="get" style="display:flex;gap:10px;flex-wrap:wrap;">
                <input type="hidden" name="lang" value="{{ lang }}">
                <select name="account">
                    <option value="">{% if lang == 'zh' %}所有账户{% else %}All Accounts{% endif %}</option>
                    {% for acc in accounts %}
                    <option value="{{ acc }}" {% if acc == selected_account %}selected{% endif %}>{{ acc }}</option>
                    {% endfor %}
                </select>
                <select name="storage_type">
                    <option value="">{% if lang == 'zh' %}所有位置{% else %}All Locations{% endif %}</option>
                    <option value="stash" {% if selected_storage == 'stash' %}selected{% endif %}>{% if lang == 'zh' %}箱子{% else %}Stash{% endif %}</option>
                    <option value="character" {% if selected_storage == 'character' %}selected{% endif %}>{% if lang == 'zh' %}角色背包{% else %}Character{% endif %}</option>
                    <option value="shared" {% if selected_storage == 'shared' %}selected{% else %}selected{% endif %}>{% if lang == 'zh' %}共享箱{% else %}Shared Stash{% endif %}</option>
                </select>
                <button type="submit" class="btn">{% if lang == 'zh' %}筛选{% else %}Filter{% endif %}</button>
            </form>
        </div>
        
        {% if items %}
        <table>
            <thead>
                <tr>
                    <th>{% if lang == 'zh' %}物品{% else %}Item{% endif %}</th>
                    <th>{% if lang == 'zh' %}账户{% else %}Account{% endif %}</th>
                    <th>{% if lang == 'zh' %}角色/位置{% else %}Character/Location{% endif %}</th>
                    <th>{% if lang == 'zh' %}属性{% else %}Stats{% endif %}</th>
                    <th>{% if lang == 'zh' %}备注{% else %}Notes{% endif %}</th>
                    <th>{% if lang == 'zh' %}操作{% else %}Actions{% endif %}</th>
                </tr>
            </thead>
            <tbody>
                {% for item in items %}
                <tr>
                    <td>
                        {% if item.item_type == 'unique' %}
                        <span style="color:#ffd700">{{ item.item_id }}</span>
                        {% elif item.item_type == 'set' %}
                        <span style="color:#00ff00">{{ item.item_id }}</span>
                        {% elif item.item_type == 'magic' %}
                        <span style="color:#8080ff">{{ item.item_id }}</span>
                        {% elif item.item_type == 'rare' %}
                        <span style="color:#ffff00">{{ item.item_id }}</span>
                        {% elif item.item_type == 'runeword' %}
                        <span style="color:#00ffff">{{ item.item_id }}</span>
                        {% else %}
                        {{ item.item_id }}
                        {% endif %}
                        {% if item.is_ethereal %}<span class="eth">{% if lang == 'zh' %}无形{% else %}(ETH){% endif %}</span>{% endif %}
                        {% if item.is_artifact %}<span style="color:#ff00ff">{% if lang == 'zh' %}神器{% else %}(ART){% endif %}</span>{% endif %}
                        {% if item.sockets and item.sockets > 0 %}<span style="color:#ffa500">({{ item.sockets }}孔)</span>{% endif %}
                    </td>
                    <td>{{ item.account }}</td>
                    <td>
                        {% if item.storage_type == 'stash' %}
                        <span class="badge badge-stash">{% if lang == 'zh' %}箱子{% else %}Stash{% endif %}</span>
                        {% elif item.storage_type == 'character' %}
                        <span class="badge badge-char">{{ item.character_name }}</span>
                        {% elif item.storage_type == 'shared' %}
                        <span class="badge badge-shared">{% if lang == 'zh' %}共享箱{% else %}Shared{% endif %}</span>
                        {% endif %}
                        {% if item.storage_name %}({{ item.storage_name }}){% endif %}
                    </td>
                    <td style="font-size:0.75em;">
                        {% if item.req_level %}[{{ item.req_level }}]{% endif %}
                        {% if item.defense %} Def: {{ item.defense }}{% endif %}
                        {% if item.enhanced_defense %} ED: {{ item.enhanced_defense }}%{% endif %}
                        {% if item.damage_min %}{{ item.damage_min }}-{{ item.damage_max or item.damage_min }}{% endif %}
                        {% if item.sockets %}[{{ item.sockets }}]{% endif %}
                        {% if item.str_bonus %}+{{ item.str_bonus }} Str{% endif %}
                        {% if item.dex_bonus %}+{{ item.dex_bonus }} Dex{% endif %}
                        {% if item.vit_bonus %}+{{ item.vit_bonus }} Vit{% endif %}
                        {% if item.ene_bonus %}+{{ item.ene_bonus }} Ene{% endif %}
                        {% if item.life %}+{{ item.life }} Life{% endif %}
                        {% if item.mana %}+{{ item.mana }} Mana{% endif %}
                        {% if item.skill_name %}+{{ item.skill_level or 1 }} {{ item.skill_name }}{% endif %}
                        {% if item.ias %}+{{ item.ias }}% IAS{% endif %}
                        {% if item.fcr %}+{{ item.fcr }}% FCR{% endif %}
                        {% if item.fhr %}+{{ item.fhr }}% FHR{% endif %}
                        {% if item.frw %}+{{ item.frw }}% FRW{% endif %}
                        {% if item.res_all %}+{{ item.res_all }}% All Res{% endif %}
                        {% if item.res_fire %}+{{ item.res_fire }}% Fire Res{% endif %}
                        {% if item.res_cold %}+{{ item.res_cold }}% Cold Res{% endif %}
                        {% if item.res_ltng %}+{{ item.res_ltng }}% Ltng Res{% endif %}
                        {% if item.mf %}+{{ item.mf }}% MF{% endif %}
                        {% if item.life_steal %}{{ item.life_steal }}% Life Steal{% endif %}
                        {% if item.cannot_be_frozen %}[CBF]{% endif %}
                    </td>
                    <td>{{ item.notes or '' }}</td>
                    <td>
                        <a href="/my-items/edit/{{ item.id }}?lang={{ lang }}" class="btn">{% if lang == 'zh' %}编辑{% else %}Edit{% endif %}</a>
                        <a href="/my-items/delete/{{ item.id }}?lang={{ lang }}" class="btn btn-danger" onclick="return confirm('{% if lang == 'zh' %}确定删除?{% else %}Confirm delete?{% endif %}')">{% if lang == 'zh' %}删除{% else %}Delete{% endif %}</a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        {% else %}
        <div class="empty">
            {% if lang == 'zh' %}暂无物品记录，点击"添加物品"开始记录{% else %}No items yet. Click "Add Item" to start tracking{% endif %}
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

MY_ITEMS_ADD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>添加物品 | Add Item</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a14; color: #ccc; min-height: 100vh; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #f0c040; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #aaa; font-weight: 500; font-size: 0.9em; }
        .col label { min-height: 20px; }
        input, select, textarea { width: 100%; padding: 10px; background: #1a1a2a; color: #fff; border: 1px solid #333; border-radius: 4px; }
        .row { display: flex; gap: 15px; }
        .col { flex: 1; }
        .btn { padding: 10px 20px; background: #4a4a5a; color: #fff; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; }
        .btn-primary { background: #f0c040; color: #000; }
        .btn:hover { opacity: 0.8; }
        .checkbox-group { display: flex; gap: 20px; align-items: center; }
        .form-section-title { color: #f0c040; border-bottom: 1px solid #444; padding-bottom: 5px; display: block; margin-bottom: 10px; font-weight: 600; }
        .upload-section { background: #1a1a30; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 2px dashed #444; text-align: center; }
        .upload-section:hover { border-color: #f0c040; }
        .upload-section input[type="file"] { display: none; }
        .upload-preview { max-width: 100%; max-height: 200px; margin-top: 10px; display: none; }
        .ocr-status { margin-top: 10px; color: #888; }
        .ocr-loading { color: #f0c040; }
        .ocr-success { color: #4f4; }
        .ocr-error { color: #f44; }
        input.filled { border-color: #4a90d9 !important; background: #1a2a3a; }
        input:focus { outline: none; border-color: #f0c040; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{% if lang == 'zh' %}添加物品{% else %}Add Item{% endif %}</h1>
        
        <div class="upload-section">
            <div style="cursor:pointer;" onclick="document.getElementById('file-input').click()">
                <div style="font-size:2em;margin-bottom:10px;">📷</div>
                <div>{% if lang == 'zh' %}点击上传物品截图，自动识别属性{% else %}Click to upload item screenshot, auto-recognize stats{% endif %}</div>
                <div style="font-size:0.8em;color:#666;margin-top:5px;">PNG, JPG, GIF</div>
            </div>
            <input type="file" id="file-input" accept="image/*" onchange="uploadImage(this)">
            <img id="preview" class="upload-preview">
            <div id="ocr-status" class="ocr-status"></div>
        </div>
        
        <form method="post" id="item-form">
            <div class="form-group">
                <label>{% if lang == 'zh' %}物品类型{% else %}Item Type{% endif %}</label>
                <div class="row">
                    <div class="col">
                        <select name="item_type" id="item_type" onchange="updateItems()">
                            <option value="normal">{% if lang == 'zh' %}普通(基础){% else %}Normal (Base){% endif %}</option>
                            <option value="magic">{% if lang == 'zh' %}魔法{% else %}Magic{% endif %}</option>
                            <option value="rare">{% if lang == 'zh' %}稀有{% else %}Rare{% endif %}</option>
                            <option value="unique">{% if lang == 'zh' %}暗金{% else %}Unique{% endif %}</option>
                            <option value="set">{% if lang == 'zh' %}套装{% else %}Set{% endif %}</option>
                            <option value="runeword">{% if lang == 'zh' %}符文之语{% else %}Runeword{% endif %}</option>
                        </select>
                    </div>
                    <div class="col">
                        <input type="text" name="item_id" id="item_id" list="item_list" placeholder="{% if lang == 'zh' %}输入搜索物品名称...{% else %}Search item name...{% endif %}">
                        <datalist id="item_list"></datalist>
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label>{% if lang == 'zh' %}战网账户{% else %}Battle.net Account{% endif %}</label>
                <input type="text" name="account" id="account_input" list="account_list" placeholder="{% if lang == 'zh' %}输入或选择账户{% else %}Type or select account{% endif %}" oninput="filterCharacters()" onchange="filterCharacters()" required>
                <datalist id="account_list">
                    {% for acc in accounts %}
                    <option value="{{ acc[1] }}">{{ acc[1] }}</option>
                    {% endfor %}
                </datalist>
                <div style="margin-top:5px;font-size:12px;color:#666;">
                    <a href="/accounts?lang={{ lang }}" target="_blank">{% if lang == 'zh' %}管理账户和角色{% else %}Manage Accounts & Characters{% endif %}</a>
                </div>
            </div>
            
            <div class="form-group">
                <label>{% if lang == 'zh' %}存储位置{% else %}Storage Location{% endif %}</label>
                <div class="row">
                    <div class="col">
                        <select name="storage_type" id="storage_type" onchange="toggleCharacter()" required>
                            <option value="stash">{% if lang == 'zh' %}箱子{% else %}Stash{% endif %}</option>
                            <option value="character">{% if lang == 'zh' %}角色背包{% else %}Character Inventory{% endif %}</option>
                            <option value="shared">{% if lang == 'zh' %}共享箱{% else %}Shared Stash{% endif %}</option>
                        </select>
                    </div>
                    <div class="col" id="char_col">
                        <input type="text" name="character_name" id="character_input" list="character_list" placeholder="{% if lang == 'zh' %}输入或选择角色{% else %}Type or select character{% endif %}">
                        <datalist id="character_list"></datalist>
                    </div>
                    <div class="col">
                        <input type="text" name="storage_name" placeholder="{% if lang == 'zh' %}箱子名(可选){% else %}Stash Name (optional){% endif %}">
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}物品属性{% else %}Item Stats{% endif %}</label>
                
                <div class="row">
                    <div class="col"><label>{% if lang == 'zh' %}等级需求{% else %}Req Level{% endif %}</label><input type="number" name="req_level"></div>
                    <div class="col"><label>{% if lang == 'zh' %}力量需求{% else %}Req Str{% endif %}</label><input type="number" name="req_str"></div>
                    <div class="col"><label>{% if lang == 'zh' %}敏捷需求{% else %}Req Dex{% endif %}</label><input type="number" name="req_dex"></div>
                </div>
                
                <div class="row" style="margin-top:10px;">
                    <div class="col"><label>{% if lang == 'zh' %}防御{% else %}Defense{% endif %}</label><input type="number" name="defense"></div>
                    <div class="col"><label>ED%</label><input type="number" name="enhanced_defense"></div>
                    <div class="col"><label>{% if lang == 'zh' %}孔数{% else %}Sockets{% endif %}</label><input type="number" name="sockets"></div>
                </div>
                
                <div class="row" style="margin-top:10px;">
                    <div class="col"><label>{% if lang == 'zh' %}耐久度{% else %}Durability{% endif %}</label><input type="number" name="durability"></div>
                    <div class="col"><label>{% if lang == 'zh' %}伤害(最小){% else %}Dmg Min{% endif %}</label><input type="number" name="damage_min"></div>
                    <div class="col"><label>{% if lang == 'zh' %}伤害(最大){% else %}Dmg Max{% endif %}</label><input type="number" name="damage_max"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}属性加成{% else %}Stat Bonuses{% endif %}</label>
                <div class="row">
                    <div class="col"><label>+Str</label><input type="number" name="str_bonus"></div>
                    <div class="col"><label>+Dex</label><input type="number" name="dex_bonus"></div>
                    <div class="col"><label>+Vit</label><input type="number" name="vit_bonus"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <div class="col"><label>+Ene</label><input type="number" name="ene_bonus"></div>
                    <div class="col"><label>+Life</label><input type="number" name="life"></div>
                    <div class="col"><label>+Mana</label><input type="number" name="mana"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}技能{% else %}Skills{% endif %}</label>
                <div class="row">
                    <div class="col">
                        <label>{% if lang == 'zh' %}技能名称{% else %}Skill Name{% endif %}</label>
                        <input type="text" name="skill_name" list="skill_list">
                        <datalist id="skill_list">
                            <option value="Fire Ball">
                            <option value="Meteor">
                            <option value="Blizzard">
                            <option value="Frozen Orb">
                            <option value="Chain Lightning">
                            <option value="Thunder Storm">
                            <option value="Blaze">
                            <option value="Fire Wall">
                            <option value="Enchant">
                            <option value="Warmth">
                            <option value="Teleport">
                            <option value="Static Field">
                            <option value="Nova">
                            <option value="Lightning">
                            <option value="Ice Blast">
                            <option value="Glacial Spike">
                            <option value="Frost Nova">
                            <option value="Shiver Armor">
                            <option value="Cold Mastery">
                            <option value="Fire Mastery">
                            <option value="Lightning Mastery">
                            <option value="Holy Bolt">
                            <option value="Holy Fire">
                            <option value="Holy Freeze">
                            <option value="Holy Shock">
                            <option value="Vengeance">
                            <option value="Judgment">
                            <option value="Fist of the Heavens">
                            <option value="Smite">
                            <option value="Holy Shield">
                            <option value="Charge">
                            <option value="Blessed Aim">
                            <option value="Fanaticism">
                            <option value="Conviction">
                            <option value="Resist Lightning">
                            <option value="Resist Fire">
                            <option value="Resist Cold">
                            <option value="Salvation">
                            <option value="Might">
                            <option value="Powerful">
                            <option value="Holy Freeze">
                            <option value="Weapon Block">
                            <option value="Sanctuary">
                            <option value="Meditation">
                            <option value="Fury">
                            <option value="Werewolf">
                            <option value="Lycanthropy">
                            <option value="Feral Rage">
                            <option value="Maul">
                            <option value="Rabies">
                            <option value="Fire Claws">
                            <option value="Hunger">
                            <option value="Shock Wave">
                            <option value="Tornado">
                            <option value="Hurricane">
                            <option value="Armageddon">
                            <option value="Volcano">
                            <option value="Corpse Explosion">
                            <option value="Bone Spear">
                            <option value="Bone Spirit">
                            <option value="Poison Nova">
                            <option value="Poison Explosion">
                            <option value="Teeth">
                            <option value="Bone Wall">
                            <option value="Bone Prison">
                            <option value="Summon Resist">
                            <option value="Iron Maiden">
                            <option value="Life Tap">
                            <option value="Attract">
                            <option value="Dim Vision">
                            <option value="Confuse">
                            <option value="Amplify Damage">
                            <option value="Decrepify">
                            <option value="Lower Resist">
                            <option value="Potion Heal">
                            <option value="Potion Mana">
                            <option value="Teleporter">
                            <option value="Skill 1">
                            <option value="Skill 2">
                            <option value="All Skills">
                        </datalist>
                    </div>
                    <div class="col"><label>{% if lang == 'zh' %}技能等级{% else %}Skill Level{% endif %}</label><input type="number" name="skill_level"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}触发技能 (CTC) #1{% else %}Chance to Cast (CTC) #1{% endif %}</label>
                <div class="row">
                    <div class="col">
                        <label>{% if lang == 'zh' %}触发条件{% else %}Trigger{% endif %}</label>
                        <select name="ctc_trigger">
                            <option value="">-</option>
                            <option value="when struck">{% if lang == 'zh' %}被击中时{% else %}When Struck{% endif %}</option>
                            <option value="on attack">{% if lang == 'zh' %}攻击时{% else %}On Attack{% endif %}</option>
                            <option value="on kill">{% if lang == 'zh' %}击杀时{% else %}On Kill{% endif %}</option>
                            <option value="on death">{% if lang == 'zh' %}死亡时{% else %}On Death{% endif %}</option>
                            <option value="on hit">{% if lang == 'zh' %}击中时{% else %}On Hit{% endif %}</option>
                        </select>
                    </div>
                    <div class="col"><label>{% if lang == 'zh' %}技能名称{% else %}Skill Name{% endif %}</label><input type="text" name="ctc_skill_name"></div>
                    <div class="col"><label>{% if lang == 'zh' %}技能等级{% else %}Skill Lvl{% endif %}</label><input type="number" name="ctc_skill_level"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}触发技能 (CTC) #2{% else %}Chance to Cast (CTC) #2{% endif %}</label>
                <div class="row">
                    <div class="col">
                        <label>{% if lang == 'zh' %}触发条件{% else %}Trigger{% endif %}</label>
                        <select name="ctc_trigger2">
                            <option value="">-</option>
                            <option value="when struck">{% if lang == 'zh' %}被击中时{% else %}When Struck{% endif %}</option>
                            <option value="on attack">{% if lang == 'zh' %}攻击时{% else %}On Attack{% endif %}</option>
                            <option value="on kill">{% if lang == 'zh' %}击杀时{% else %}On Kill{% endif %}</option>
                            <option value="on death">{% if lang == 'zh' %}死亡时{% else %}On Death{% endif %}</option>
                            <option value="on hit">{% if lang == 'zh' %}击中时{% else %}On Hit{% endif %}</option>
                        </select>
                    </div>
                    <div class="col"><label>{% if lang == 'zh' %}技能名称{% else %}Skill Name{% endif %}</label><input type="text" name="ctc_skill_name2"></div>
                    <div class="col"><label>{% if lang == 'zh' %}技能等级{% else %}Skill Lvl{% endif %}</label><input type="number" name="ctc_skill_level2"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}触发技能 (CTC) #3{% else %}Chance to Cast (CTC) #3{% endif %}</label>
                <div class="row">
                    <div class="col">
                        <label>{% if lang == 'zh' %}触发条件{% else %}Trigger{% endif %}</label>
                        <select name="ctc_trigger3">
                            <option value="">-</option>
                            <option value="when struck">{% if lang == 'zh' %}被击中时{% else %}When Struck{% endif %}</option>
                            <option value="on attack">{% if lang == 'zh' %}攻击时{% else %}On Attack{% endif %}</option>
                            <option value="on kill">{% if lang == 'zh' %}击杀时{% else %}On Kill{% endif %}</option>
                            <option value="on death">{% if lang == 'zh' %}死亡时{% else %}On Death{% endif %}</option>
                            <option value="on hit">{% if lang == 'zh' %}击中时{% else %}On Hit{% endif %}</option>
                        </select>
                    </div>
                    <div class="col"><label>{% if lang == 'zh' %}技能名称{% else %}Skill Name{% endif %}</label><input type="text" name="ctc_skill_name3"></div>
                    <div class="col"><label>{% if lang == 'zh' %}技能等级{% else %}Skill Lvl{% endif %}</label><input type="number" name="ctc_skill_level3"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}速度/施法/格挡{% else %}Speed/Cast/Block{% endif %}</label>
                <div class="row">
                    <div class="col"><label>IAS%</label><input type="number" name="ias"></div>
                    <div class="col"><label>FCR%</label><input type="number" name="fcr"></div>
                    <div class="col"><label>FHR%</label><input type="number" name="fhr"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <div class="col"><label>FRW%</label><input type="number" name="frw"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}抗性{% else %}Resistances{% endif %}</label>
                <div class="row">
                    <div class="col"><label>{% if lang == 'zh' %}火抗{% else %}Fire Res{% endif %}</label><input type="number" name="res_fire"></div>
                    <div class="col"><label>{% if lang == 'zh' %}冰抗{% else %}Cold Res{% endif %}</label><input type="number" name="res_cold"></div>
                    <div class="col"><label>{% if lang == 'zh' %}电抗{% else %}Ltng Res{% endif %}</label><input type="number" name="res_ltng"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <div class="col"><label>{% if lang == 'zh' %}毒抗{% else %}Poison Res{% endif %}</label><input type="number" name="res_pois"></div>
                    <div class="col"><label>{% if lang == 'zh' %}全抗{% else %}All Res{% endif %}</label><input type="number" name="res_all"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}吸收{% else %}Absorb{% endif %}</label>
                <div class="row">
                    <div class="col"><label>{% if lang == 'zh' %}火吸收{% else %}Fire Abs{% endif %}</label><input type="number" name="absorb_fire"></div>
                    <div class="col"><label>{% if lang == 'zh' %}冰吸收{% else %}Cold Abs{% endif %}</label><input type="number" name="absorb_cold"></div>
                    <div class="col"><label>{% if lang == 'zh' %}电吸收{% else %}Ltng Abs{% endif %}</label><input type="number" name="absorb_ltng"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}元素伤害{% else %}Elemental Damage{% endif %}</label>
                <div class="row">
                    <div class="col"><label>{% if lang == 'zh' %}火伤min{% else %}Fire Min{% endif %}</label><input type="number" name="add_fire_min"></div>
                    <div class="col"><label>{% if lang == 'zh' %}火伤max{% else %}Fire Max{% endif %}</label><input type="number" name="add_fire_max"></div>
                    <div class="col"><label>{% if lang == 'zh' %}冰伤min{% else %}Cold Min{% endif %}</label><input type="number" name="add_cold_min"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <div class="col"><label>{% if lang == 'zh' %}冰伤max{% else %}Cold Max{% endif %}</label><input type="number" name="add_cold_max"></div>
                    <div class="col"><label>{% if lang == 'zh' %}电伤min{% else %}Ltng Min{% endif %}</label><input type="number" name="add_ltng_min"></div>
                    <div class="col"><label>{% if lang == 'zh' %}电伤max{% else %}Ltng Max{% endif %}</label><input type="number" name="add_ltng_max"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <div class="col"><label>{% if lang == 'zh' %}毒伤min{% else %}Poison Min{% endif %}</label><input type="number" name="add_pois_min"></div>
                    <div class="col"><label>{% if lang == 'zh' %}毒伤max{% else %}Poison Max{% endif %}</label><input type="number" name="add_pois_max"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}MF/GF/偷取{% else %}MF/GF/Life-Mana{% endif %}</label>
                <div class="row">
                    <div class="col"><label>MF%</label><input type="number" name="mf"></div>
                    <div class="col"><label>EG%</label><input type="number" name="eg"></div>
                    <div class="col"><label>{% if lang == 'zh' %}生命偷取%{% else %}Life Steal{% endif %}</label><input type="number" name="life_steal"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <div class="col"><label>{% if lang == 'zh' %}魔法偷取%{% else %}Mana Steal{% endif %}</label><input type="number" name="mana_steal"></div>
                    <div class="col"><label>{% if lang == 'zh' %}击杀生命{% else %}Life/Kill{% endif %}</label><input type="number" name="life_after_kill"></div>
                    <div class="col"><label>{% if lang == 'zh' %}击杀魔法{% else %}Mana/Kill{% endif %}</label><input type="number" name="mana_after_kill"></div>
                </div>
            </div>
            
            <div class="form-group">
                <label style="color:#f0c040;border-bottom:1px solid #444;padding-bottom:5px;display:block;margin-bottom:10px;">{% if lang == 'zh' %}攻击属性{% else %}Combat Stats{% endif %}</label>
                <div class="row">
                    <div class="col"><label>AR%</label><input type="number" name="attack_rating"></div>
                    <div class="col"><label>+AR</label><input type="number" name="attack_rating_plus"></div>
                    <div class="col"><label>CB%</label><input type="number" name="crushing_blow"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <div class="col"><label>DS%</label><input type="number" name="deadly_strike"></div>
                    <div class="col"><label>OW%</label><input type="number" name="open_wounds"></div>
                </div>
            </div>
            
            <div class="form-group checkbox-group">
                <input type="checkbox" name="cannot_be_frozen" id="cannot_be_frozen" style="width:auto;">
                <label for="cannot_be_frozen" style="display:inline;margin:0;">{% if lang == 'zh' %}无法冰冻{% else %}Cannot Be Frozen{% endif %}</label>
            </div>
            
            <div class="form-group checkbox-group">
                <input type="checkbox" name="is_ethereal" id="is_ethereal" style="width:auto;">
                <label for="is_ethereal" style="display:inline;margin:0;">{% if lang == 'zh' %}无形{% else %}Ethereal{% endif %}</label>
                <span style="width:20px"></span>
                <input type="checkbox" name="is_artifact" id="is_artifact" style="width:auto;">
                <label for="is_artifact" style="display:inline;margin:0;">{% if lang == 'zh' %}神器{% else %}Artifact{% endif %}</label>
            </div>
            
            <div class="form-group">
                <label>{% if lang == 'zh' %}备注{% else %}Notes{% endif %}</label>
                <textarea name="notes" rows="3" placeholder="{% if lang == 'zh' %}其他信息...{% else %}Additional info...{% endif %}"></textarea>
            </div>
            
            <div style="display:flex;gap:10px;">
                <button type="submit" class="btn btn-primary">{% if lang == 'zh' %}保存{% else %}Save{% endif %}</button>
                <a href="/my-items?lang={{ lang }}" class="btn">{% if lang == 'zh' %}取消{% else %}Cancel{% endif %}</a>
            </div>
        </form>
    </div>
    <script>
        const uniqueItems = {{ unique_items|tojson }};
        const setItems = {{ set_items|tojson }};
        const weapons = {{ weapons|tojson }};
        const armors = {{ armors|tojson }};
        const miscItems = {{ misc_items|tojson }};
        
        function updateItems() {
            const type = document.getElementById('item_type').value;
            const datalist = document.getElementById('item_list');
            datalist.innerHTML = '';
            
            let items = [];
            if (type === 'unique') items = uniqueItems;
            else if (type === 'set') items = setItems;
            else if (type === 'normal') items = [...weapons, ...armors, ...miscItems];
            else if (type === 'magic') items = [...weapons, ...armors, ...miscItems];
            else if (type === 'rare') items = [...weapons, ...armors, ...miscItems];
            else if (type === 'runeword') items = [...weapons, ...armors, ...miscItems];
            
            items.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item[0];
                opt.textContent = item[0] + (item[1] ? ' (' + item[1] + ')' : '');
                datalist.appendChild(opt);
            });
        }
        
        function uploadImage(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                const formData = new FormData();
                formData.append('file', file);
                
                const status = document.getElementById('ocr-status');
                status.innerHTML = '<span class="ocr-loading">{% if lang == "zh" %}正在识别图片...{% else %}Recognizing image...{% endif %}</span>';
                
                fetch('/upload-item-image', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('preview').src = data.image_url;
                        document.getElementById('preview').style.display = 'block';
                        status.innerHTML = '<span class="ocr-success">{% if lang == "zh" %}识别成功！请检查下方属性{% else %}Recognition successful!{% endif %}</span>';
                        
                        const item = data.item_data;
                        if (item.item_name) document.getElementById('item_id').value = item.item_name;
                        if (item.req_level) setFormValue('req_level', item.req_level);
                        if (item.req_str) setFormValue('req_str', item.req_str);
                        if (item.req_dex) setFormValue('req_dex', item.req_dex);
                        if (item.defense) setFormValue('defense', item.defense);
                        if (item.enhanced_defense) setFormValue('enhanced_defense', item.enhanced_defense);
                        if (item.damage_min) setFormValue('damage_min', item.damage_min);
                        if (item.damage_max) setFormValue('damage_max', item.damage_max);
                        if (item.durability) setFormValue('durability', item.durability);
                        if (item.sockets) setFormValue('sockets', item.sockets);
                        if (item.str_bonus) setFormValue('str_bonus', item.str_bonus);
                        if (item.dex_bonus) setFormValue('dex_bonus', item.dex_bonus);
                        if (item.vit_bonus) setFormValue('vit_bonus', item.vit_bonus);
                        if (item.ene_bonus) setFormValue('ene_bonus', item.ene_bonus);
                        if (item.life) setFormValue('life', item.life);
                        if (item.mana) setFormValue('mana', item.mana);
                        if (item.skill_name) setFormValue('skill_name', item.skill_name);
                        if (item.skill_level) setFormValue('skill_level', item.skill_level);
                        if (item.ias) setFormValue('ias', item.ias);
                        if (item.fcr) setFormValue('fcr', item.fcr);
                        if (item.fhr) setFormValue('fhr', item.fhr);
                        if (item.frw) setFormValue('frw', item.frw);
                        if (item.res_fire) setFormValue('res_fire', item.res_fire);
                        if (item.res_cold) setFormValue('res_cold', item.res_cold);
                        if (item.res_ltng) setFormValue('res_ltng', item.res_ltng);
                        if (item.res_pois) setFormValue('res_pois', item.res_pois);
                        if (item.res_all) setFormValue('res_all', item.res_all);
                        if (item.mf) setFormValue('mf', item.mf);
                        if (item.life_steal) setFormValue('life_steal', item.life_steal);
                        if (item.mana_steal) setFormValue('mana_steal', item.mana_steal);
                        if (item.life_after_kill) setFormValue('life_after_kill', item.life_after_kill);
                        if (item.mana_after_kill) setFormValue('mana_after_kill', item.mana_after_kill);
                        if (item.cannot_be_frozen) document.getElementById('cannot_be_frozen').checked = true;
                        if (item.is_ethereal) document.getElementById('is_ethereal').checked = true;
                        if (item.add_fire_min) setFormValue('add_fire_min', item.add_fire_min);
                        if (item.add_fire_max) setFormValue('add_fire_max', item.add_fire_max);
                        if (item.add_cold_min) setFormValue('add_cold_min', item.add_cold_min);
                        if (item.add_cold_max) setFormValue('add_cold_max', item.add_cold_max);
                        if (item.add_ltng_min) setFormValue('add_ltng_min', item.add_ltng_min);
                        if (item.add_ltng_max) setFormValue('add_ltng_max', item.add_ltng_max);
                        if (item.add_pois_min) setFormValue('add_pois_min', item.add_pois_min);
                        if (item.add_pois_max) setFormValue('add_pois_max', item.add_pois_max);
                        if (item.absorb_fire) setFormValue('absorb_fire', item.absorb_fire);
                        if (item.absorb_cold) setFormValue('absorb_cold', item.absorb_cold);
                        if (item.absorb_ltng) setFormValue('absorb_ltng', item.absorb_ltng);
                        if (item.crushing_blow) setFormValue('crushing_blow', item.crushing_blow);
                        if (item.deadly_strike) setFormValue('deadly_strike', item.deadly_strike);
                        if (item.open_wounds) setFormValue('open_wounds', item.open_wounds);
                        
                        let imgInput = document.getElementById('image_path');
                        if (!imgInput) {
                            imgInput = document.createElement('input');
                            imgInput.type = 'hidden';
                            imgInput.name = 'image_path';
                            imgInput.id = 'image_path';
                            document.getElementById('item-form').appendChild(imgInput);
                        }
                        imgInput.value = data.image_url;
                    } else {
                        status.innerHTML = '<span class="ocr-error">' + (data.error || 'Error') + '</span>';
                    }
                })
                .catch(error => {
                    status.innerHTML = '<span class="ocr-error">Error: ' + error + '</span>';
                });
            }
        }
        
        function setFormValue(name, value) {
            const el = document.querySelector('input[name="' + name + '"]');
            if (el) {
                el.value = value;
                el.classList.add('filled');
            }
        }
        
        updateItems();
        
        const accountsData = {{ accounts|tojson }};
        const charactersData = {{ characters|tojson }};
        
        function filterCharacters() {
            const accountInput = document.getElementById('account_input');
            const characterList = document.getElementById('character_list');
            const selectedAccount = accountInput.value.trim();
            
            characterList.innerHTML = '';
            
            if (!selectedAccount) {
                charactersData.forEach(char => {
                    const opt = document.createElement('option');
                    opt.value = char[2];
                    opt.textContent = char[2] + (char[3] ? ' (' + char[3] + ')' : '');
                    characterList.appendChild(opt);
                });
                return;
            }
            
            const matchedAccount = accountsData.find(acc => acc[1] === selectedAccount);
            if (!matchedAccount) {
                return;
            }
            
            const accountId = matchedAccount[0];
            const filteredChars = charactersData.filter(char => char[1] === accountId);
            
            filteredChars.forEach(char => {
                const opt = document.createElement('option');
                opt.value = char[2];
                opt.textContent = char[2] + (char[3] ? ' (' + char[3] + ')' : '');
                characterList.appendChild(opt);
            });
        }
        
        function toggleCharacter() {
            const storageType = document.getElementById('storage_type').value;
            const charCol = document.getElementById('char_col');
            const charInput = document.getElementById('character_input');
            
            if (storageType === 'character') {
                charCol.style.display = 'block';
                charInput.required = true;
            } else {
                charCol.style.display = 'block';
                charInput.required = false;
            }
        }
        
        filterCharacters();
    </script>
</body>
</html>
'''

MY_ITEMS_EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>编辑物品 | Edit Item</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a14; color: #ccc; min-height: 100vh; }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #f0c040; margin-bottom: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #888; }
        input, select, textarea { width: 100%; padding: 10px; background: #1a1a2a; color: #fff; border: 1px solid #333; border-radius: 4px; }
        .row { display: flex; gap: 15px; }
        .col { flex: 1; }
        .btn { padding: 10px 20px; background: #4a4a5a; color: #fff; text-decoration: none; border-radius: 4px; border: none; cursor: pointer; }
        .btn-primary { background: #f0c040; color: #000; }
        .btn:hover { opacity: 0.8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{% if lang == 'zh' %}编辑物品{% else %}Edit Item{% endif %}</h1>
        <form method="post">
            <div class="form-group">
                <label>{% if lang == 'zh' %}物品类型{% else %}Item Type{% endif %}</label>
                <div class="row">
                    <div class="col">
                        <select name="item_type" id="item_type" onchange="updateItems()">
                            <option value="normal" {% if item.item_type == 'normal' %}selected{% endif %}>{% if lang == 'zh' %}普通(基础){% else %}Normal (Base){% endif %}</option>
                            <option value="magic" {% if item.item_type == 'magic' %}selected{% endif %}>{% if lang == 'zh' %}魔法{% else %}Magic{% endif %}</option>
                            <option value="rare" {% if item.item_type == 'rare' %}selected{% endif %}>{% if lang == 'zh' %}稀有{% else %}Rare{% endif %}</option>
                            <option value="unique" {% if item.item_type == 'unique' %}selected{% endif %}>{% if lang == 'zh' %}暗金{% else %}Unique{% endif %}</option>
                            <option value="set" {% if item.item_type == 'set' %}selected{% endif %}>{% if lang == 'zh' %}套装{% else %}Set{% endif %}</option>
                            <option value="runeword" {% if item.item_type == 'runeword' %}selected{% endif %}>{% if lang == 'zh' %}符文之语{% else %}Runeword{% endif %}</option>
                        </select>
                    </div>
                    <div class="col">
                        <input type="text" name="item_id" id="item_id" value="{{ item.item_id or '' }}" list="item_list" placeholder="{% if lang == 'zh' %}输入搜索物品名称...{% else %}Search item name...{% endif %}">
                        <datalist id="item_list"></datalist>
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label>{% if lang == 'zh' %}战网账户{% else %}Battle.net Account{% endif %}</label>
                <input type="text" name="account" id="account_input" value="{{ item.account }}" list="account_list" placeholder="{% if lang == 'zh' %}输入或选择账户{% else %}Type or select account{% endif %}" oninput="filterCharacters()" onchange="filterCharacters()" required>
                <datalist id="account_list">
                    {% for acc in accounts %}
                    <option value="{{ acc[1] }}">{{ acc[1] }}</option>
                    {% endfor %}
                </datalist>
            </div>
            
            <div class="form-group">
                <label>{% if lang == 'zh' %}存储位置{% else %}Storage Location{% endif %}</label>
                <div class="row">
                    <div class="col">
                        <select name="storage_type" id="storage_type" onchange="toggleCharacter()" required>
                            <option value="stash" {% if item.storage_type == 'stash' %}selected{% endif %}>{% if lang == 'zh' %}箱子{% else %}Stash{% endif %}</option>
                            <option value="character" {% if item.storage_type == 'character' %}selected{% endif %}>{% if lang == 'zh' %}角色背包{% else %}Character{% endif %}</option>
                            <option value="shared" {% if item.storage_type == 'shared' %}selected{% endif %}>{% if lang == 'zh' %}共享箱{% else %}Shared Stash{% endif %}</option>
                        </select>
                    </div>
                    <div class="col" id="char_col">
                        <input type="text" name="character_name" id="character_input" value="{{ item.character_name or '' }}" list="character_list" placeholder="{% if lang == 'zh' %}输入或选择角色{% else %}Type or select character{% endif %}">
                        <datalist id="character_list"></datalist>
                    </div>
                    <div class="col">
                        <input type="text" name="storage_name" value="{{ item.storage_name or '' }}" placeholder="{% if lang == 'zh' %}箱子名{% else %}Stash Name{% endif %}">
                    </div>
                </div>
            </div>
            
            <div class="form-group">
                <label>{% if lang == 'zh' %}物品属性{% else %}Item Stats{% endif %}</label>
                <div class="row">
                    <div class="col"><input type="number" name="quality" value="{{ item.quality or '' }}" placeholder="{% if lang == 'zh' %}品质{% else %}Quality{% endif %}"></div>
                    <div class="col"><input type="number" name="defense" value="{{ item.defense or '' }}" placeholder="{% if lang == 'zh' %}防御{% else %}Defense{% endif %}"></div>
                    <div class="col"><input type="number" name="enhanced_damage" value="{{ item.enhanced_damage or '' }}" placeholder="ED%"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <div class="col"><input type="number" name="skills" value="{{ item.skills or '' }}" placeholder="{% if lang == 'zh' %}技能{% else %}Skills{% endif %}"></div>
                    <div class="col"><input type="number" name="all_resists" value="{{ item.all_resists or '' }}" placeholder="{% if lang == 'zh' %}全抗{% else %}Resists{% endif %}"></div>
                    <div class="col"><input type="number" name="mf" value="{{ item.mf or '' }}" placeholder="MF%"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <div class="col"><input type="number" name="sockets" value="{{ item.sockets or '' }}" placeholder="{% if lang == 'zh' %}孔数{% else %}Sockets{% endif %}"></div>
                </div>
            </div>
            
            <div class="form-group checkbox-group">
                <input type="checkbox" name="is_ethereal" id="is_ethereal" {% if item.is_ethereal %}checked{% endif %} style="width:auto;">
                <label for="is_ethereal" style="display:inline;margin:0;">{% if lang == 'zh' %}无形{% else %}Ethereal{% endif %}</label>
                <span style="width:20px"></span>
                <input type="checkbox" name="is_artifact" id="is_artifact" {% if item.is_artifact %}checked{% endif %} style="width:auto;">
                <label for="is_artifact" style="display:inline;margin:0;">{% if lang == 'zh' %}神器{% else %}Artifact{% endif %}</label>
            </div>
            
            <div class="form-group">
                <label>{% if lang == 'zh' %}备注{% else %}Notes{% endif %}</label>
                <textarea name="notes" rows="3">{{ item.notes or '' }}</textarea>
            </div>
            
            <div style="display:flex;gap:10px;">
                <button type="submit" class="btn btn-primary">{% if lang == 'zh' %}保存{% else %}Save{% endif %}</button>
                <a href="/my-items?lang={{ lang }}" class="btn">{% if lang == 'zh' %}取消{% else %}Cancel{% endif %}</a>
            </div>
        </form>
    </div>
    <script>
        const uniqueItems = {{ unique_items|tojson }};
        const setItems = {{ set_items|tojson }};
        const weapons = {{ weapons|tojson }};
        const armors = {{ armors|tojson }};
        const miscItems = {{ misc_items|tojson }};
        
        function updateItems() {
            const type = document.getElementById('item_type').value;
            const datalist = document.getElementById('item_list');
            datalist.innerHTML = '';
            
            let items = [];
            if (type === 'unique') items = uniqueItems;
            else if (type === 'set') items = setItems;
            else if (type === 'normal') items = [...weapons, ...armors, ...miscItems];
            else if (type === 'magic') items = [...weapons, ...armors, ...miscItems];
            else if (type === 'rare') items = [...weapons, ...armors, ...miscItems];
            else if (type === 'runeword') items = [...weapons, ...armors, ...miscItems];
            
            items.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item[0];
                opt.textContent = item[0] + (item[1] ? ' (' + item[1] + ')' : '');
                datalist.appendChild(opt);
            });
        }
        
        updateItems();
        
        const accountsData = {{ accounts|tojson }};
        const charactersData = {{ characters|tojson }};
        
        function filterCharacters() {
            const accountInput = document.getElementById('account_input');
            const characterList = document.getElementById('character_list');
            const selectedAccount = accountInput.value.trim();
            
            characterList.innerHTML = '';
            
            if (!selectedAccount) {
                charactersData.forEach(char => {
                    const opt = document.createElement('option');
                    opt.value = char[2];
                    opt.textContent = char[2] + (char[3] ? ' (' + char[3] + ')' : '');
                    characterList.appendChild(opt);
                });
                return;
            }
            
            const matchedAccount = accountsData.find(acc => acc[1] === selectedAccount);
            if (!matchedAccount) {
                return;
            }
            
            const accountId = matchedAccount[0];
            const filteredChars = charactersData.filter(char => char[1] === accountId);
            
            filteredChars.forEach(char => {
                const opt = document.createElement('option');
                opt.value = char[2];
                opt.textContent = char[2] + (char[3] ? ' (' + char[3] + ')' : '');
                characterList.appendChild(opt);
            });
        }
        
        function toggleCharacter() {
            const storageType = document.getElementById('storage_type').value;
            const charCol = document.getElementById('char_col');
            const charInput = document.getElementById('character_input');
            
            if (storageType === 'character') {
                charCol.style.display = 'block';
                charInput.required = true;
            } else {
                charCol.style.display = 'block';
                charInput.required = false;
            }
        }
        
        filterCharacters();
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
