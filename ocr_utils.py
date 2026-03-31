import re
import easyocr
import os

_reader = None

def get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _reader

def extract_item_from_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    try:
        reader = get_reader()
        results = reader.readtext(image_path)
        
        text_lines = []
        for (bbox, text, prob) in results:
            if text.strip():
                text_lines.append(text.strip())
        
        full_text = '\n'.join(text_lines)
        
        if not full_text.strip():
            raise ValueError("No text detected in image")
        
        return parse_d2r_item(full_text)
    except Exception as e:
        raise Exception(f"OCR Error: {str(e)}")

def parse_d2r_item(text):
    item = {}
    
    # 物品名称 (通常在第一行)
    lines = text.split('\n')
    if lines:
        item['item_name'] = lines[0].strip()
    
    # 等级需求
    match = re.search(r'Req\s*Level[:\s]*(\d+)', text, re.I)
    if match:
        item['req_level'] = int(match.group(1))
    
    # 力量需求
    match = re.search(r'Req\s*Strength[:\s]*(\d+)', text, re.I)
    if match:
        item['req_str'] = int(match.group(1))
    
    # 敏捷需求  
    match = re.search(r'Req\s*Dexterity[:\s]*(\d+)', text, re.I)
    if match:
        item['req_dex'] = int(match.group(1))
    
    # 防御
    match = re.search(r'Defense[:\s]*(\d+)', text, re.I)
    if match:
        item['defense'] = int(match.group(1))
    
    # 增强防御
    match = re.search(r'(\d+)-(\d+)\s*Enhanced\s*Defense', text, re.I)
    if match:
        item['enhanced_defense'] = int(match.group(1))
    
    # 伤害
    match = re.search(r'Damage[:\s]*(\d+)-(\d+)', text, re.I)
    if match:
        item['damage_min'] = int(match.group(1))
        item['damage_max'] = int(match.group(2))
    
    # 耐久度
    match = re.search(r'Durability[:\s]*(\d+)', text, re.I)
    if match:
        item['durability'] = int(match.group(1))
    
    # 孔数
    match = re.search(r'Socket[s]?\s*\((\d+)\s*to\s*(\d+)\)', text, re.I)
    if match:
        item['sockets'] = int(match.group(2))
    match = re.search(r'(\d+)\s*Socket[s]?', text, re.I)
    if match and 'sockets' not in item:
        item['sockets'] = int(match.group(1))
    
    # +力量
    match = re.search(r'\+(\d+)\s*to\s*Strength', text, re.I)
    if match:
        item['str_bonus'] = int(match.group(1))
    
    # +敏捷
    match = re.search(r'\+(\d+)\s*to\s*Dexterity', text, re.I)
    if match:
        item['dex_bonus'] = int(match.group(1))
    
    # +体力
    match = re.search(r'\+(\d+)\s*to\s*Vitality', text, re.I)
    if match:
        item['vit_bonus'] = int(match.group(1))
    
    # +能量
    match = re.search(r'\+(\d+)\s*to\s*Energy', text, re.I)
    if match:
        item['ene_bonus'] = int(match.group(1))
    
    # +生命
    match = re.search(r'\+(\d+)\s*to\s*Life', text, re.I)
    if match:
        item['life'] = int(match.group(1))
    
    # +魔法
    match = re.search(r'\+(\d+)\s*to\s*Mana', text, re.I)
    if match:
        item['mana'] = int(match.group(1))
    
    # +所有技能
    match = re.search(r'\+(\d+)\s*to\s*All\s*Skills', text, re.I)
    if match:
        item['skill_name'] = 'All Skills'
        item['skill_level'] = int(match.group(1))
    
    # IAS - 攻速
    match = re.search(r'(\d+)%\s*Faster\s*Attack\s*Speed', text, re.I)
    if match:
        item['ias'] = int(match.group(1))
    match = re.search(r'\+(\d+)%\s*IAS', text, re.I)
    if match:
        item['ias'] = int(match.group(1))
    
    # FCR - 施法速度
    match = re.search(r'(\d+)%\s*Faster\s*Cast\s*Rate', text, re.I)
    if match:
        item['fcr'] = int(match.group(1))
    
    # FHR - 命中恢复
    match = re.search(r'(\d+)%\s*Faster\s*Hit\s*Recovery', text, re.I)
    if match:
        item['fhr'] = int(match.group(1))
    
    # FRW - 跑速
    match = re.search(r'(\d+)%\s*Faster\s*Run/Walk', text, re.I)
    if match:
        item['frw'] = int(match.group(1))
    
    # 抗性
    match = re.search(r'\+(\d+)%\s*to\s*Fire\s*Resist', text, re.I)
    if match:
        item['res_fire'] = int(match.group(1))
    
    match = re.search(r'\+(\d+)%\s*to\s*Cold\s*Resist', text, re.I)
    if match:
        item['res_cold'] = int(match.group(1))
    
    match = re.search(r'\+(\d+)%\s*to\s*Lightning\s*Resist', text, re.I)
    if match:
        item['res_ltng'] = int(match.group(1))
    
    match = re.search(r'\+(\d+)%\s*to\s*Poison\s*Resist', text, re.I)
    if match:
        item['res_pois'] = int(match.group(1))
    
    match = re.search(r'\+(\d+)%\s*to\s*All\s*Resist', text, re.I)
    if match:
        item['res_all'] = int(match.group(1))
    
    # MF
    match = re.search(r'(\d+)%\s*Better\s*Chance\s*of\s*Getting\s*Magic\s*Items', text, re.I)
    if match:
        item['mf'] = int(match.group(1))
    
    # 生命偷取
    match = re.search(r'(\d+)%\s*Life\s*Stolen\s*Per\s*Hit', text, re.I)
    if match:
        item['life_steal'] = float(match.group(1))
    
    # 魔法偷取
    match = re.search(r'(\d+)%\s*Mana\s*Stolen\s*Per\s*Hit', text, re.I)
    if match:
        item['mana_steal'] = float(match.group(1))
    
    # 击杀生命
    match = re.search(r'(\d+)-(\d+)\s*Life\s*after\s*each\s*Kill', text, re.I)
    if match:
        item['life_after_kill'] = int(match.group(1))
    
    # 击杀魔法
    match = re.search(r'(\d+)\s*Mana\s*after\s*each\s*Kill', text, re.I)
    if match:
        item['mana_after_kill'] = int(match.group(1))
    
    # 无法冰冻
    if re.search(r'Cannot\s*Be\s*Frozen', text, re.I):
        item['cannot_be_frozen'] = 1
    
    # 元素伤害
    match = re.search(r'Adds\s*(\d+)-(\d+)\s*Cold\s*Damage', text, re.I)
    if match:
        item['add_cold_min'] = int(match.group(1))
        item['add_cold_max'] = int(match.group(2))
    
    match = re.search(r'Adds\s*(\d+)-(\d+)\s*Fire\s*Damage', text, re.I)
    if match:
        item['add_fire_min'] = int(match.group(1))
        item['add_fire_max'] = int(match.group(2))
    
    match = re.search(r'Adds\s*(\d+)-(\d+)\s*Lightning\s*Damage', text, re.I)
    if match:
        item['add_ltng_min'] = int(match.group(1))
        item['add_ltng_max'] = int(match.group(2))
    
    match = re.search(r'Adds\s*(\d+)-(\d+)\s*Poison\s*Damage', text, re.I)
    if match:
        item['add_pois_min'] = int(match.group(1))
        item['add_pois_max'] = int(match.group(2))
    
    # 吸收
    match = re.search(r'(\d+)%\s*Cold\s*Absorb', text, re.I)
    if match:
        item['absorb_cold'] = int(match.group(1))
    
    match = re.search(r'(\d+)%\s*Fire\s*Absorb', text, re.I)
    if match:
        item['absorb_fire'] = int(match.group(1))
    
    match = re.search(r'(\d+)%\s*Lightning\s*Absorb', text, re.I)
    if match:
        item['absorb_ltng'] = int(match.group(1))
    
    # 无形
    if re.search(r'Ethereal', text, re.I):
        item['is_ethereal'] = 1
    
    # 压碎打击
    match = re.search(r'(\d+)%\s*Crushing\s*Blow', text, re.I)
    if match:
        item['crushing_blow'] = int(match.group(1))
    
    # 致命打击
    match = re.search(r'(\d+)%\s*Deadly\s*Strike', text, re.I)
    if match:
        item['deadly_strike'] = int(match.group(1))
    
    # 撕裂伤口
    match = re.search(r'(\d+)%\s*Open\s*Wounds', text, re.I)
    if match:
        item['open_wounds'] = int(match.group(1))
    
    # 经验获取
    match = re.search(r'(\d+)%\s*To\s*Experience\s*Gain', text, re.I)
    if match:
        item['experience'] = int(match.group(1))
    
    # 目标防御
    match = re.search(r'(\d+)%\s*Target\s*Defense', text, re.I)
    if match:
        item['target_defense'] = int(match.group(1))
    
    # 伤害转魔法
    match = re.search(r'(\d+)%\s*Damage\s*To\s*Mana', text, re.I)
    if match:
        item['dmg_to_mana'] = int(match.group(1))
    
    # 攻击评级
    match = re.search(r'\+(\d+)\s*Attack\s*Rating', text, re.I)
    if match:
        item['attack_rating_plus'] = int(match.group(1))
    
    # 攻击评级%
    match = re.search(r'(\d+)%\s*to\s*Attack\s*Rating', text, re.I)
    if match:
        item['attack_rating'] = int(match.group(1))
    
    # 物理伤害减少
    match = re.search(r'(\d+)\s*Damage\s*Reduced\s*By', text, re.I)
    if match:
        item['damage_reduced'] = int(match.group(1))
    
    # 魔法伤害减少
    match = re.search(r'(\d+)\s*Magic\s*Damage\s*Reduced\s*By', text, re.I)
    if match:
        item['magic_damage_reduced'] = int(match.group(1))
    
    # 荆棘
    match = re.search(r'(\d+)\s*Life\s*Regenerated\s*Per\s*Second', text, re.I)
    if match:
        item['life_regen'] = int(match.group(1))
    
    # 魔法泉涌
    match = re.search(r'(\d+)\s*Mana\s*Regen', text, re.I)
    if match:
        item['mana_regen'] = int(match.group(1))
    
    # 减少魔法消耗
    match = re.search(r'(\d+)%\s*Reduced\s*Mana\s*Cost', text, re.I)
    if match:
        item['reduce_mana_cost'] = int(match.group(1))
    
    # 需求降低
    match = re.search(r'(\d+)%\s*Reduced\s*Item\s*Requirements', text, re.I)
    if match:
        item['reduce_requirements'] = int(match.group(1))
    
    # 生命汲取
    match = re.search(r'Replenish\s*Life\s*(\d+)', text, re.I)
    if match:
        item['replenish_life'] = int(match.group(1))
    
    # 快速施法/攻击/格挡恢复
    match = re.search(r'(\d+)%\s*Faster\s*Block\s*Rate', text, re.I)
    if match:
        item['fbr'] = int(match.group(1))
    
    # 吸收生命
    match = re.search(r'Life\s*Absorb\s*(\d+)', text, re.I)
    if match:
        item['absorb_life'] = int(match.group(1))
    
    # 吸收魔法
    match = re.search(r'Mana\s*Absorb\s*(\d+)', text, re.I)
    if match:
        item['absorb_mana'] = int(match.group(1))
    
    # 完整文本（用于手动查看）
    item['full_text'] = text
    
    return item
