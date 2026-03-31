import os

file_path = "broadcast_timer.py"
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

operator_html = []
in_operator = False
for i, line in enumerate(lines):
    if line.startswith("OPERATOR_HTML = \"\"\""):
        in_operator = True
        continue
    elif in_operator and line.startswith("\"\"\""):
        break
    elif in_operator:
        operator_html.append(line)

with open("web/operator.html", "w", encoding="utf-8") as f:
    f.writelines(operator_html)


index_html = []
in_index = False
for i, line in enumerate(lines):
    if "html = \"\"\"" in line:
        in_index = True
        continue
    elif in_index and line.strip().startswith("\"\"\""):
        break
    elif in_index:
        # Strip the leading indentation for neatness if needed
        # But for exact preservation:
        index_html.append(line)

with open("web/index.html", "w", encoding="utf-8") as f:
    f.writelines(index_html)
