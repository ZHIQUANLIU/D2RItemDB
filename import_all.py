import sqlite3
import os
import csv
import json

DATA_DIR = "data"
DB_PATH = "d2r_full.db"

def safe_int(val, default=0):
    try:
        return int(val) if val and val.strip() else default
    except:
        return default

def read_tsv(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f, delimiter='\t')
        rows = list(reader)
        if not rows:
            return [], []
        headers = [h.strip() for h in rows[0]]
        data = rows[1:]
        return headers, data

def get_table_name(filename):
    return os.path.splitext(filename)[0]

def import_all_files():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.txt')]
    total = 0
    
    for filename in sorted(files):
        filepath = os.path.join(DATA_DIR, filename)
        table_name = get_table_name(filename)
        
        try:
            headers, data = read_tsv(filepath)
            if not headers:
                print(f"Skipping {filename}: no headers")
                continue
            
            # Handle duplicate column names - add suffix to duplicates
            col_count = {}
            unique_headers = []
            for h in headers:
                h_clean = h.strip()
                if h_clean in col_count:
                    col_count[h_clean] += 1
                    unique_headers.append(f"{h_clean}_{col_count[h_clean]}")
                else:
                    col_count[h_clean] = 0
                    unique_headers.append(h_clean)
            
            col_defs = []
            for i, h in enumerate(unique_headers):
                # Add index suffix to avoid any duplicate column name issues
                col_defs.append(f'"{h}_{i}" TEXT')
            
            create_sql = f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY, {', '.join(col_defs)})"
            cursor.execute(create_sql)
            
            count = 0
            for row in data:
                if len(row) == 0:
                    continue
                if len(row) < len(unique_headers):
                    row.extend([''] * (len(unique_headers) - len(row)))
                
                values = []
                for i, val in enumerate(row[:len(unique_headers)]):
                    values.append(val.strip() if val else '')
                
                placeholders = ','.join(['?'] * (len(unique_headers) + 1))
                cursor.execute(f"INSERT INTO {table_name} VALUES ({placeholders})", [None] + values)
                count += 1
            
            conn.commit()
            print(f"{table_name}: {count} rows")
            total += count
        except Exception as e:
            print(f"Error importing {filename}: {e}")
    
    conn.close()
    print(f"\nTotal: {total} rows imported")

if __name__ == "__main__":
    import_all_files()
