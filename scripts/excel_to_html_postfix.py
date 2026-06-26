import re
from pathlib import Path


DEFAULT_COUNTER_THEME = "asoul"
DEFAULT_COUNTER_HEIGHT_PX = 24
MIN_COUNTER_HEIGHT_PX = 8
MAX_COUNTER_HEIGHT_PX = 128
ALLOWED_COUNTER_THEMES = {"asoul", "moebooru", "rule34"}
LEGACY_COUNTER_IDS = {
    "ruth-oyen-ro": "ruth_oyen",
}
COUNTER_MARKER_RE = re.compile(
    r"A\s*(?:<span\b[^>]*display\s*:\s*none[^>]*>\s*)?"
    r"CCESS_COUNTER\s*(?::\s*([A-Za-z0-9_-]+))?"
    r"\s*(?::\s*([A-Za-z0-9_-]+))?"
    r"\s*(?::\s*([0-9]+))?\s*(?:</span>)?",
    re.IGNORECASE,
)
COUNTER_CELL_RE = re.compile(
    r"(<td\b[^>]*>)"
    r"((?:(?!</td>).)*COUNTER(?:(?!</td>).)*)"
    r"(</td>)",
    re.IGNORECASE | re.DOTALL,
)
COUNTER_EXISTING_RE = re.compile(
    r'(?:<span\b[^>]*>\s*)?'
    r'<img\s+src="https://counter\.256server\.com/([A-Za-z0-9_-]+)\?theme=([A-Za-z0-9_-]+)"[^>]*>'
    r'(?:\s*</span>)?(?:&nbsp;)?',
    re.IGNORECASE,
)

HEAD_INSERT = """<meta charset="UTF-8">
<title>RL78 Board Index | Ruth Oyen</title>
<meta name="description" content="RL78/G1X, G2X series development boards and writers by Ruth Oyen.">
<link rel="stylesheet" href="style.css">
"""


def insert_head_metadata(html):
    if '<meta charset="UTF-8">' in html:
        return html
    return html.replace("<head>", f"<head>\n{HEAD_INSERT}", 1)


def remove_head_metadata(html):
    return html.replace(HEAD_INSERT, "", 1)


def validate_theme(theme):
    if theme not in ALLOWED_COUNTER_THEMES:
        allowed = ", ".join(sorted(ALLOWED_COUNTER_THEMES))
        raise ValueError(f"Access counter theme must be one of: {allowed}")
    return theme


def validate_height(height_px):
    if height_px < MIN_COUNTER_HEIGHT_PX or height_px > MAX_COUNTER_HEIGHT_PX:
        raise ValueError(
            "Access counter height must be "
            f"{MIN_COUNTER_HEIGHT_PX}-{MAX_COUNTER_HEIGHT_PX}px"
        )
    return height_px


def counter_img(
    counter_id,
    theme=DEFAULT_COUNTER_THEME,
    height_px=DEFAULT_COUNTER_HEIGHT_PX,
):
    theme = validate_theme(theme)
    height_px = validate_height(height_px)
    counter_url = f"https://counter.256server.com/{counter_id}?theme={theme}"
    return (
        '<span style="position:absolute;z-index:1000;line-height:0">'
        f'<img src="{counter_url}" alt="Access counter" '
        f'style="display:block;border:0;height:{height_px}px;width:auto" '
        'referrerpolicy="no-referrer-when-downgrade">'
        '</span>&nbsp;'
    )


def existing_counter_img(match):
    height_match = re.search(r"height\s*:\s*([0-9]+)px", match.group(0))
    height_px = (
        int(height_match.group(1)) if height_match else DEFAULT_COUNTER_HEIGHT_PX
    )
    return counter_img(
        LEGACY_COUNTER_IDS.get(match.group(1), match.group(1)),
        match.group(2),
        height_px,
    )


def marker_config(marker_html):
    marker_text = re.sub(r"<[^>]+>", "", marker_html)
    marker_text = re.sub(r"\s+", "", marker_text)
    match = re.search(
        r"ACCESS_COUNTER(?::([A-Za-z0-9_-]+))?"
        r"(?::([A-Za-z0-9_-]+))?(?::([0-9]+))?",
        marker_text,
        flags=re.IGNORECASE,
    )
    if not match or not match.group(1):
        raise ValueError(
            "Access counter marker must be "
            "ACCESS_COUNTER:<counter_id>:<theme>:<height_px>"
        )
    height_px = (
        int(match.group(3)) if match.group(3) else DEFAULT_COUNTER_HEIGHT_PX
    )
    return match.group(1), match.group(2) or DEFAULT_COUNTER_THEME, height_px


def insert_access_counter(html):
    if "counter.256server.com" in html:
        return COUNTER_EXISTING_RE.sub(
            existing_counter_img,
            html,
            count=1,
        )

    def replace_marker_cell(match):
        counter_id, theme, height_px = marker_config(match.group(2))
        return (
            f"{match.group(1)}"
            f"{counter_img(counter_id, theme, height_px)}"
            f"{match.group(3)}"
        )

    updated = COUNTER_CELL_RE.sub(replace_marker_cell, html, count=1)
    if updated != html:
        return updated

    def replace_marker(match):
        counter_id = match.group(1)
        if not counter_id:
            raise ValueError(
                "Access counter marker must be "
                "ACCESS_COUNTER:<counter_id>:<theme>:<height_px>"
            )
        theme = match.group(2) or DEFAULT_COUNTER_THEME
        height_px = (
            int(match.group(3)) if match.group(3) else DEFAULT_COUNTER_HEIGHT_PX
        )
        return counter_img(counter_id, theme, height_px)

    return COUNTER_MARKER_RE.sub(replace_marker, html, count=1)


def main():
    html_files = (Path("index.html"), Path("index.files/sheet001.html"))

    changed = []
    for html_file in html_files:
        if not html_file.exists():
            continue

        html = html_file.read_text(encoding="utf-8")
        updated = insert_access_counter(html)
        if html_file.name == "index.html":
            updated = insert_head_metadata(updated)
        else:
            updated = remove_head_metadata(updated)
        if updated != html:
            html_file.write_text(updated, encoding="utf-8")
            changed.append(str(html_file))

    if changed:
        print(f"Post-processed: {', '.join(changed)}")
    else:
        print("Post-process: no changes needed.")


if __name__ == "__main__":
    main()
