import glob, re

for file in glob.glob('templates/*.html'):
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update header links
    content = re.sub(
        r'<a href="[^"]*settings[^"]*" style="[^"]*">({% .*? %})</a>',
        r'<a href="/settings?lang={{ lang }}" class="btn">\1</a>',
        content
    )
    content = re.sub(
        r'<a href="[^"]*my-items[^"]*" style="[^"]*">({% .*? %})</a>',
        r'<a href="/my-items?lang={{ lang }}" class="btn accent">\1</a>',
        content
    )

    # Update language switch
    content = re.sub(
        r'<div class="lang-switch">.*?</div>',
        r'<div class="tabs" style="margin-bottom:0;">\n                    <button class="tab {% if lang==\'zh\' %}active{% endif %}" onclick="setLang(\'zh\')">中文</button>\n                    <button class="tab {% if lang==\'en\' %}active{% endif %}" onclick="setLang(\'en\')">English</button>\n                </div>',
        content, flags=re.DOTALL
    )

    # Wrap item icon
    content = re.sub(
        r'(<img [^>]*class="item-icon"[^>]*>)',
        r'<div class="item-icon-wrap">\1</div>',
        content
    )

    # Update form inputs to use input-field
    content = re.sub(
        r'<input type="(text|password|number)"([^>]*)(?<!class="input-field")>',
        r'<input type="\1" class="input-field"\2>',
        content
    )

    # Ensure buttons have btn class
    content = re.sub(
        r'<button type="submit"(.*?)>',
        r'<button type="submit" class="btn primary"\1>',
        content
    )

    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)

print('Updated classes in templates.')
