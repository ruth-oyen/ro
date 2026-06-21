from pathlib import Path

html_file = Path("index.html")
html = html_file.read_text(encoding="utf-8")

insert = """<meta charset="UTF-8">
<title>RL78 Board Index | Ruth Oyen</title>
<meta name="description" content="RL78/G1X, G2X series development boards and writers by Ruth Oyen.">
<link rel="stylesheet" href="style.css">
"""

html = html.replace("<head>", f"<head>\n{insert}")
html_file.write_text(html, encoding="utf-8")

print("✅ Meta information has been added.")
