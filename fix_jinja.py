import glob

for file in glob.glob('templates/*.html'):
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i in range(len(lines)):
        if "onclick=\"showModal(" in lines[i]:
            # Replace the entire line with a data-attribute version
            # Because the string replacements inside Jinja tags are failing
            indent = len(lines[i]) - len(lines[i].lstrip())
            new_line = " " * indent + "<button class=\"raw-btn\" data-title=\"{{ item.unique_name or item.set_item_name or item.name }}\" data-raw=\"{{ item.raw_data|e }}\" onclick=\"showModal(this.dataset.title, this.dataset.raw)\">{{ '原始数据' if lang=='zh' else 'Raw Data' }}</button>\n"
            lines[i] = new_line
            
    with open(file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
