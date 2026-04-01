import os
import re

app_path = "app.py"
with open(app_path, "r", encoding="utf-8") as f:
    app_text = f.read()

# 1. Update imports
if "from flask import" in app_text:
    app_text = re.sub(r"from flask import ([^\n]+)", r"from flask import render_template, \1", app_text, count=1)
    app_text = app_text.replace("render_template_string,", "")
    app_text = app_text.replace("render_template_string", "render_template") # Some exact matches

# Template mappings
templates = {
    "ACCOUNTS_TEMPLATE": "accounts.html",
    "HTML_TEMPLATE": "index.html",
    "MY_ITEMS_TEMPLATE": "my_items.html",
    "MY_ITEMS_ADD_TEMPLATE": "my_items_add.html",
    "MY_ITEMS_EDIT_TEMPLATE": "my_items_edit.html"
}

os.makedirs("templates", exist_ok=True)

# 2. Extract, transform and save templates, and remove from app.py
for tpl_name, filename in templates.items():
    # Find the template string using regex. It looks like:
    # CONSTANT_TEMPLATE = '''...''' or """...""" or f'''...'''
    pattern = rf"{tpl_name}\s*=\s*(f?[']{{3}}|f?[\"]{{3}})(.*?)\1"
    match = re.search(pattern, app_text, re.DOTALL)
    if match:
        full_def = match.group(0)
        content = match.group(2)
        
        # We need to strip <head>, <style>, body tags
        # Find everything between <div class="container"> or <body> and </body>
        body_content = content
        
        # Try to find container or body
        container_match = re.search(r'(<div class="container">.*)</body>', content, re.DOTALL)
        if container_match:
            body_content = container_match.group(1)
            
            # Extract script tags and put them at the end
            scripts = ""
            script_match = re.search(r'(<script>.*?</script>)', content, re.DOTALL)
            if script_match and script_match.group(1) not in body_content:
                scripts = script_match.group(1)
            elif script_match:
                 pass # already in body_content usually
            
            # We want to replace `<style>...</style>` if it got caught, but it's usually in head.
            
            final_html = f"{{% extends 'base.html' %}}\n{{% block content %}}\n{body_content}\n{{% endblock %}}"
        else:
            final_html = content # fallback
            
        with open(f"templates/{filename}", "w", encoding="utf-8") as f:
            f.write(final_html)
            
        # Remove definition from app.py
        app_text = app_text.replace(full_def, f"# {tpl_name} moved to templates/{filename}")
        print(f"Migrated {tpl_name} -> templates/{filename}")
        
        # 3. Replace render_template_string usages
        # Sometimes it's render_template_string(HTML_TEMPLATE, ...) -> render_template('index.html', ...)
        app_text = app_text.replace(f"render_template_string({tpl_name},", f"render_template('{filename}',")
        app_text = app_text.replace(f"render_template_string({tpl_name})", f"render_template('{filename}')")

# The Settings template is inline in @app.route('/settings')
settings_pattern = r"return f?[']{3}(.*?<title>Settings</title>.*?)[']{3}"
settings_match = re.search(settings_pattern, app_text, re.DOTALL)
if settings_match:
    full_return = settings_match.group(0)
    html_content = settings_match.group(1)
    
    body_match = re.search(r'(<div class="container">.*)</body>', html_content, re.DOTALL)
    if body_match:
        body_content = body_match.group(1)
        final_settings = f"{{% extends 'base.html' %}}\n{{% block content %}}\n{body_content}\n{{% endblock %}}"
        with open("templates/settings.html", "w", encoding="utf-8") as f:
            f.write(final_settings)
        print("Migrated settings template")
        
        # Replace the return statement
        app_text = app_text.replace(full_return, "return render_template('settings.html', lang=lang, s=s)")

# Write back
with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_text)
print("Finished refactoring app.py")
