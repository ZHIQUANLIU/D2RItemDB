import sqlite3
import os
import csv
import json

DATA_DIR = "data"
DB_PATH = "d2r_items.db"

def read_tsv(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f, delimiter='\t')
        rows = list(reader)
        if not rows:
            return [], []
        headers = [h.strip() for h in rows[0]]
        data = rows[1:]
        return headers, data

def create_tables(conn):
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS weapons")
    cursor.execute("""
        CREATE TABLE weapons (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,
            type2 TEXT,
            code TEXT,
            mindam INTEGER,
            maxdam INTEGER,
            speed INTEGER,
            reqstr INTEGER,
            reqdex INTEGER,
            durability INTEGER,
            nodurability INTEGER,
            level INTEGER,
            levelreq INTEGER,
            cost INTEGER,
            gamble_cost INTEGER,
            magic_lvl INTEGER,
            sockets INTEGER,
            wclass TEXT,
            invwidth INTEGER,
            invheight INTEGER,
            useable TEXT,
            raw_data TEXT
        )
    """)
    
    cursor.execute("DROP TABLE IF EXISTS armor")
    cursor.execute("""
        CREATE TABLE armor (
            id INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,
            type2 TEXT,
            code TEXT,
            minac INTEGER,
            maxac INTEGER,
            speed INTEGER,
            reqstr INTEGER,
            reqdex INTEGER,
            block INTEGER,
            durability INTEGER,
            nodurability INTEGER,
            level INTEGER,
            levelreq INTEGER,
            cost INTEGER,
            gamble_cost INTEGER,
            magic_lvl INTEGER,
            sockets INTEGER,
            invwidth INTEGER,
            invheight INTEGER,
            useable TEXT,
            raw_data TEXT
        )
    """)
    
    cursor.execute("DROP TABLE IF EXISTS unique_items")
    cursor.execute("""
        CREATE TABLE unique_items (
            id INTEGER PRIMARY KEY,
            index_name TEXT,
            name TEXT,
            code TEXT,
            level INTEGER,
            levelreq INTEGER,
            rarity INTEGER,
            cost_mult INTEGER,
            cost_add INTEGER,
            props TEXT,
            raw_data TEXT
        )
    """)
    
    cursor.execute("DROP TABLE IF EXISTS set_items")
    cursor.execute("""
        CREATE TABLE set_items (
            id INTEGER PRIMARY KEY,
            index_name TEXT,
            set_name TEXT,
            name TEXT,
            code TEXT,
            level INTEGER,
            levelreq INTEGER,
            rarity INTEGER,
            cost_mult INTEGER,
            props TEXT,
            raw_data TEXT
        )
    """)
    
    cursor.execute("DROP TABLE IF EXISTS misc")
    cursor.execute("""
        CREATE TABLE misc (
            id INTEGER PRIMARY KEY,
            name TEXT,
            code TEXT,
            type TEXT,
            type2 TEXT,
            level INTEGER,
            levelreq INTEGER,
            cost INTEGER,
            useable TEXT,
            raw_data TEXT
        )
    """)
    
    cursor.execute("DROP TABLE IF EXISTS gems")
    cursor.execute("""
        CREATE TABLE gems (
            id INTEGER PRIMARY KEY,
            name TEXT,
            code TEXT,
            type TEXT,
            level INTEGER,
            raw_data TEXT
        )
    """)
    
    cursor.execute("DROP TABLE IF EXISTS runes")
    cursor.execute("""
        CREATE TABLE runes (
            id INTEGER PRIMARY KEY,
            name TEXT,
            complete INTEGER,
            itype1 TEXT,
            itype2 TEXT,
            rune1 TEXT,
            rune2 TEXT,
            rune3 TEXT,
            rune4 TEXT,
            rune5 TEXT,
            rune6 TEXT,
            props TEXT,
            raw_data TEXT
        )
    """)
    
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_item_images_code ON item_images(code)")

    conn.commit()

def safe_int(val, default=0):
    try:
        return int(val) if val and val.strip() else default
    except:
        return default

def get_all_cols(headers, row):
    result = {}
    for i, h in enumerate(headers):
        if i < len(row):
            val = row[i].strip() if row[i] else ''
            if val:
                result[h] = val
    return result

def import_weapons(conn, filepath):
    headers, data = read_tsv(filepath)
    cursor = conn.cursor()
    
    def gi(*names):
        for n in names:
            if n in headers: return headers.index(n)
        return -1
    
    count = 0
    for row in data:
        if len(row) == 0: continue
        if gi('name') < 0 or gi('code') < 0: continue
        if gi('name') >= len(row) or gi('code') >= len(row): continue
        if not row[gi('name')].strip() or not row[gi('code')].strip(): continue
        
        raw = get_all_cols(headers, row)
        
        cursor.execute("""
            INSERT INTO weapons (name, type, type2, code, mindam, maxdam, speed, reqstr, reqdex, durability, nodurability, level, levelreq, cost, gamble_cost, magic_lvl, sockets, wclass, invwidth, invheight, useable, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row[gi('name')].strip(),
            row[gi('type')].strip() if gi('type') >= 0 and gi('type') < len(row) else '',
            row[gi('type2')].strip() if gi('type2') >= 0 and gi('type2') < len(row) else '',
            row[gi('code')].strip(),
            safe_int(row[gi('mindam')]),
            safe_int(row[gi('maxdam')]),
            safe_int(row[gi('speed')]),
            safe_int(row[gi('reqstr')]),
            safe_int(row[gi('reqdex')]),
            safe_int(row[gi('durability')]),
            safe_int(row[gi('nodurability')]),
            safe_int(row[gi('level')]),
            safe_int(row[gi('levelreq')]),
            safe_int(row[gi('cost')]),
            safe_int(row[gi('gamble cost')]),
            safe_int(row[gi('magic lvl')]),
            safe_int(row[gi('gemsockets')]),
            row[gi('wclass')].strip() if gi('wclass') >= 0 else '',
            safe_int(row[gi('invwidth')]),
            safe_int(row[gi('invheight')]),
            row[gi('useable')].strip() if gi('useable') >= 0 else '',
            json.dumps(raw, ensure_ascii=False)
        ))
        count += 1
    
    conn.commit()
    print(f"Imported weapons: {count} items")

def import_armor(conn, filepath):
    headers, data = read_tsv(filepath)
    cursor = conn.cursor()
    
    def gi(*names):
        for n in names:
            if n in headers: return headers.index(n)
        return -1
    
    count = 0
    for row in data:
        if len(row) == 0: continue
        if gi('name') < 0 or gi('code') < 0: continue
        if gi('name') >= len(row) or gi('code') >= len(row): continue
        if not row[gi('name')].strip() or not row[gi('code')].strip(): continue
        
        raw = get_all_cols(headers, row)
        
        cursor.execute("""
            INSERT INTO armor (name, type, type2, code, minac, maxac, speed, reqstr, reqdex, block, durability, nodurability, level, levelreq, cost, gamble_cost, magic_lvl, sockets, invwidth, invheight, useable, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row[gi('name')].strip(),
            row[gi('type')].strip() if gi('type') >= 0 and gi('type') < len(row) else '',
            row[gi('type2')].strip() if gi('type2') >= 0 and gi('type2') < len(row) else '',
            row[gi('code')].strip(),
            safe_int(row[gi('minac')]),
            safe_int(row[gi('maxac')]),
            safe_int(row[gi('speed')]),
            safe_int(row[gi('reqstr')]),
            safe_int(row[gi('reqdex')]),
            safe_int(row[gi('block')]),
            safe_int(row[gi('durability')]),
            safe_int(row[gi('nodurability')]),
            safe_int(row[gi('level')]),
            safe_int(row[gi('levelreq')]),
            safe_int(row[gi('cost')]),
            safe_int(row[gi('gamble cost')]),
            safe_int(row[gi('magic lvl')]),
            safe_int(row[gi('gemsockets')]),
            safe_int(row[gi('invwidth')]),
            safe_int(row[gi('invheight')]),
            row[gi('useable')].strip() if gi('useable') >= 0 else '',
            json.dumps(raw, ensure_ascii=False)
        ))
        count += 1
    
    conn.commit()
    print(f"Imported armor: {count} items")

def import_unique_items(conn, filepath):
    headers, data = read_tsv(filepath)
    cursor = conn.cursor()
    
    def gi(*names):
        for n in names:
            if n in headers: return headers.index(n)
        return -1
    
    prop_idxs = []
    for i in range(1, 13):
        p = gi(f'prop{i}')
        if p >= 0:
            prop_idxs.append((p, gi(f'par{i}'), gi(f'min{i}'), gi(f'max{i}')))
    
    count = 0
    for row in data:
        if len(row) == 0: continue
        if gi('*ItemName') < 0 or gi('code') < 0: continue
        if gi('*ItemName') >= len(row) or gi('code') >= len(row): continue
        if not row[gi('*ItemName')].strip() or not row[gi('code')].strip(): continue
        
        props = []
        for pi, pari, mini, maxi in prop_idxs:
            if pi < len(row) and row[pi].strip():
                s = row[pi].strip()
                if pari >= 0 and pari < len(row) and row[pari].strip():
                    s += f"({row[pari].strip()})"
                if mini >= 0 and mini < len(row) and row[mini].strip():
                    s += f" {row[mini].strip()}"
                if maxi >= 0 and maxi < len(row) and row[maxi].strip():
                    s += f"-{row[maxi].strip()}"
                props.append(s)
        
        raw = get_all_cols(headers, row)
        
        cursor.execute("""
            INSERT INTO unique_items (index_name, name, code, level, levelreq, rarity, cost_mult, cost_add, props, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row[gi('index')].strip() if gi('index') >= 0 else '',
            row[gi('*ItemName')].strip(),
            row[gi('code')].strip(),
            safe_int(row[gi('lvl')]),
            safe_int(row[gi('lvl req')]),
            safe_int(row[gi('rarity')]),
            safe_int(row[gi('cost mult')]),
            safe_int(row[gi('cost add')]),
            ', '.join(props),
            json.dumps(raw, ensure_ascii=False)
        ))
        count += 1
    
    conn.commit()
    print(f"Imported unique items: {count} items")

def import_set_items(conn, filepath):
    headers, data = read_tsv(filepath)
    cursor = conn.cursor()
    
    def gi(*names):
        for n in names:
            if n in headers: return headers.index(n)
        return -1
    
    prop_idxs = []
    for i in range(1, 13):
        p = gi(f'prop{i}')
        if p >= 0:
            prop_idxs.append((p, gi(f'par{i}'), gi(f'min{i}'), gi(f'max{i}')))
    
    count = 0
    for row in data:
        if len(row) == 0: continue
        name_i = gi('*ItemName')
        code_i = gi('code')
        if name_i < 0 or code_i < 0:
            name_i = gi('item')
            code_i = gi('item')
        if name_i < 0 or code_i < 0: continue
        if name_i >= len(row) or code_i >= len(row): continue
        if not row[name_i].strip() or not row[code_i].strip(): continue
        
        props = []
        for pi, pari, mini, maxi in prop_idxs:
            if pi < len(row) and row[pi].strip():
                s = row[pi].strip()
                if pari >= 0 and pari < len(row) and row[pari].strip():
                    s += f"({row[pari].strip()})"
                if mini >= 0 and mini < len(row) and row[mini].strip():
                    s += f" {row[mini].strip()}"
                if maxi >= 0 and maxi < len(row) and row[maxi].strip():
                    s += f"-{row[maxi].strip()}"
                props.append(s)
        
        raw = get_all_cols(headers, row)
        
        cursor.execute("""
            INSERT INTO set_items (index_name, set_name, name, code, level, levelreq, rarity, cost_mult, props, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row[gi('index')].strip() if gi('index') >= 0 else '',
            row[gi('set')].strip() if gi('set') >= 0 else '',
            row[name_i].strip(),
            row[code_i].strip(),
            safe_int(row[gi('lvl')]),
            safe_int(row[gi('lvl req')]),
            safe_int(row[gi('rarity')]),
            safe_int(row[gi('cost mult')]),
            ', '.join(props),
            json.dumps(raw, ensure_ascii=False)
        ))
        count += 1
    
    conn.commit()
    print(f"Imported set items: {count} items")

def import_misc(conn, filepath):
    headers, data = read_tsv(filepath)
    cursor = conn.cursor()
    
    def gi(*names):
        for n in names:
            if n in headers: return headers.index(n)
        return -1
    
    count = 0
    for row in data:
        if len(row) == 0: continue
        if gi('name') < 0 or gi('code') < 0: continue
        if gi('name') >= len(row) or gi('code') >= len(row): continue
        if not row[gi('name')].strip() or not row[gi('code')].strip(): continue
        
        raw = get_all_cols(headers, row)
        
        cursor.execute("""
            INSERT INTO misc (name, code, type, type2, level, levelreq, cost, useable, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row[gi('name')].strip(),
            row[gi('code')].strip(),
            row[gi('type')].strip() if gi('type') >= 0 and gi('type') < len(row) else '',
            row[gi('type2')].strip() if gi('type2') >= 0 and gi('type2') < len(row) else '',
            safe_int(row[gi('level')]),
            safe_int(row[gi('levelreq')]),
            safe_int(row[gi('cost')]),
            row[gi('useable')].strip() if gi('useable') >= 0 else '',
            json.dumps(raw, ensure_ascii=False)
        ))
        count += 1
    
    conn.commit()
    print(f"Imported misc: {count} items")

def import_gems(conn, filepath):
    headers, data = read_tsv(filepath)
    cursor = conn.cursor()
    
    def gi(*names):
        for n in names:
            if n in headers: return headers.index(n)
        return -1
    
    count = 0
    for row in data:
        if len(row) == 0: continue
        if gi('name') < 0 or gi('code') < 0: continue
        if gi('name') >= len(row) or gi('code') >= len(row): continue
        if not row[gi('name')].strip() or not row[gi('code')].strip(): continue
        
        raw = get_all_cols(headers, row)
        
        cursor.execute("""
            INSERT INTO gems (name, code, type, level, raw_data)
            VALUES (?, ?, ?, ?, ?)
        """, (
            row[gi('name')].strip(),
            row[gi('code')].strip(),
            row[gi('type')].strip() if gi('type') >= 0 else '',
            safe_int(row[gi('level')]),
            json.dumps(raw, ensure_ascii=False)
        ))
        count += 1
    
    conn.commit()
    print(f"Imported gems: {count} items")

def import_runes(conn, filepath):
    headers, data = read_tsv(filepath)
    cursor = conn.cursor()
    
    def gi(*names):
        for n in names:
            if n in headers: return headers.index(n)
        return -1
    
    prop_idxs = []
    for i in range(1, 8):
        code_i = gi(f'T1Code{i}')
        if code_i >= 0:
            prop_idxs.append((code_i, gi(f'T1Param{i}'), gi(f'T1Min{i}'), gi(f'T1Max{i}')))
    
    count = 0
    for row in data:
        if len(row) == 0: continue
        name_i = gi('*Rune Name')
        if name_i < 0: name_i = gi('Name')
        if name_i < 0 or name_i >= len(row): continue
        if not row[name_i].strip(): continue
        
        props = []
        for pi, Pari, mini, maxi in prop_idxs:
            if pi < len(row) and row[pi].strip():
                s = row[pi].strip()
                if Pari >= 0 and Pari < len(row) and row[Pari].strip():
                    s += f"({row[Pari].strip()})"
                if mini >= 0 and mini < len(row) and row[mini].strip():
                    s += f" {row[mini].strip()}"
                if maxi >= 0 and maxi < len(row) and row[maxi].strip():
                    s += f"-{row[maxi].strip()}"
                props.append(s)
        
        raw = get_all_cols(headers, row)
        
        cursor.execute("""
            INSERT INTO runes (name, complete, itype1, itype2, rune1, rune2, rune3, rune4, rune5, rune6, props, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row[name_i].strip(),
            safe_int(row[gi('complete')]),
            row[gi('itype1')].strip() if gi('itype1') >= 0 else '',
            row[gi('itype2')].strip() if gi('itype2') >= 0 else '',
            row[gi('Rune1')].strip() if gi('Rune1') >= 0 else '',
            row[gi('Rune2')].strip() if gi('Rune2') >= 0 else '',
            row[gi('Rune3')].strip() if gi('Rune3') >= 0 else '',
            row[gi('Rune4')].strip() if gi('Rune4') >= 0 else '',
            row[gi('Rune5')].strip() if gi('Rune5') >= 0 else '',
            row[gi('Rune6')].strip() if gi('Rune6') >= 0 else '',
            ', '.join(props),
            json.dumps(raw, ensure_ascii=False)
        ))
        count += 1
    
    conn.commit()
    print(f"Imported runes: {count} items")

if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)
    
    import_weapons(conn, os.path.join(DATA_DIR, "weapons.txt"))
    import_armor(conn, os.path.join(DATA_DIR, "armor.txt"))
    import_unique_items(conn, os.path.join(DATA_DIR, "uniqueitems.txt"))
    import_set_items(conn, os.path.join(DATA_DIR, "setitems.txt"))
    import_misc(conn, os.path.join(DATA_DIR, "misc.txt"))
    import_gems(conn, os.path.join(DATA_DIR, "gems.txt"))
    import_runes(conn, os.path.join(DATA_DIR, "runes.txt"))
    
    conn.close()
    print(f"Database created: {DB_PATH}")
