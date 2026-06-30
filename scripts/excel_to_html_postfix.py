import html
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


COUNTER_MARKER_PATTERN = (
    r"\{\{\s*(?:<span\b[^>]*display\s*:\s*none[^>]*>\s*)?"
    r"ACCESS_COUNTER"
    r"(?:\s*:\s*(?P<center_x>[0-9]+(?:\.[0-9]+)?)"
    r"\s*:\s*(?P<center_y>[0-9]+(?:\.[0-9]+)?))?"
    r"\s*\}\}\s*(?:</span>)?"
)
COUNTER_MARKER_RE = re.compile(
    COUNTER_MARKER_PATTERN,
    re.IGNORECASE,
)
COUNTER_CELL_RE = re.compile(
    r"(?P<open_tag><td\b[^>]*>)\s*"
    + COUNTER_MARKER_PATTERN
    + r"\s*</td>",
    re.IGNORECASE | re.DOTALL,
)
COUNTER_EXISTING_RE = re.compile(
    r'<img\s+src="https?://counter\.256server\.com/[^\"]+"[^>]*>',
    re.IGNORECASE,
)

HEAD_INSERT = """<meta charset="UTF-8">
<title>RL78 Board Index | Ruth Oyen</title>
<meta name="description" content="RL78/G1X, G2X series development boards and writers by Ruth Oyen.">
<link rel="stylesheet" href="style.css">
"""


def insert_head_metadata(html_text):
    if '<meta charset="UTF-8">' in html_text:
        return html_text
    return html_text.replace("<head>", f"<head>\n{HEAD_INSERT}", 1)


def remove_head_metadata(html_text):
    return html_text.replace(HEAD_INSERT, "", 1)


def read_counter_url():
    counter_file = Path(__file__).with_name("counter.txt")
    counter_url = counter_file.read_text(encoding="utf-8").strip()
    parts = urlsplit(counter_url)

    if parts.scheme not in {"http", "https"}:
        raise ValueError("Access counter URL must use HTTP or HTTPS")
    if parts.netloc != "counter.256server.com":
        raise ValueError("Access counter URL must use counter.256server.com")
    if not parts.path:
        raise ValueError("Access counter URL must include a counter path")

    if parts.scheme == "http":
        parts = parts._replace(scheme="https")

    return urlunsplit(parts)


def counter_image_tag(counter_url):
    escaped_url = html.escape(counter_url, quote=True)
    return (
        f'<img src="{escaped_url}" alt="Access counter" '
        'style="display:block;border:0" '
        'referrerpolicy="no-referrer-when-downgrade">'
    )


def counter_img(counter_url, center_x_pt=None, center_y_pt=None):
    position_style = "position:absolute;z-index:1000;line-height:0"
    if center_x_pt is not None and center_y_pt is not None:
        position_style += (
            f";left:{center_x_pt}pt;top:{center_y_pt}pt"
            ";transform:translate(-50%,-50%)"
        )

    return (
        f'<span style="{position_style}">'
        f'{counter_image_tag(counter_url)}'
        '</span>&nbsp;'
    )


def positioned_cell_tag(open_tag):
    style_match = re.search(
        r"style=(?P<quote>['\"])(?P<style>.*?)(?P=quote)",
        open_tag,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if style_match:
        style = style_match.group("style").rstrip(";")
        replacement = (
            f"style={style_match.group('quote')}"
            f"{style};position:relative"
            f"{style_match.group('quote')}"
        )
        return (
            open_tag[:style_match.start()]
            + replacement
            + open_tag[style_match.end():]
        )

    return open_tag[:-1] + ' style="position:relative">'


def insert_access_counter(html_text, counter_url):
    updated, replacement_count = COUNTER_EXISTING_RE.subn(
        counter_image_tag(counter_url),
        html_text,
        count=1,
    )

    if replacement_count:
        return updated

    def replace_marker_cell(match):
        center_x = match.group("center_x")
        center_y = match.group("center_y")
        return (
            positioned_cell_tag(match.group("open_tag"))
            + counter_img(counter_url, center_x, center_y)
            + "</td>"
        )

    updated, replacement_count = COUNTER_CELL_RE.subn(
        replace_marker_cell,
        html_text,
        count=1,
    )
    if replacement_count:
        return updated

    return COUNTER_MARKER_RE.sub(
        lambda match: counter_img(counter_url),
        html_text,
        count=1,
    )


def main():
    html_files = (Path("index.html"), Path("index.files/sheet001.html"))
    counter_url = read_counter_url()

    changed = []
    for html_file in html_files:
        if not html_file.exists():
            continue

        html_text = html_file.read_text(encoding="utf-8")
        updated = insert_access_counter(html_text, counter_url)
        if html_file.name == "index.html":
            updated = insert_head_metadata(updated)
        else:
            updated = remove_head_metadata(updated)
        if updated != html_text:
            html_file.write_text(updated, encoding="utf-8")
            changed.append(str(html_file))

    if changed:
        print(f"Post-processed: {', '.join(changed)}")
    else:
        print("Post-process: no changes needed.")


if __name__ == "__main__":
    main()
