import argparse
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

XML_TARGETS = {
    "docProps/core.xml",
    "docProps/app.xml",
    "xl/workbook.xml",
}

LOCAL_PATH_PATTERNS = re.compile(
    r"C:[/\\](?:work|Users)\\b|OneDrive|absPath",
    re.IGNORECASE,
)

CORE_NS = {
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
}
APP_NS = {
    "ep": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties",
}


def sanitize_xml(name, text):
    original = text

    if name == "docProps/core.xml":
        text = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator></dc:creator>", text)
        text = re.sub(
            r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>",
            "<cp:lastModifiedBy></cp:lastModifiedBy>",
            text,
        )
    elif name == "docProps/app.xml":
        text = re.sub(r"<Company>.*?</Company>", "<Company></Company>", text)
        text = re.sub(r"<Manager>.*?</Manager>", "<Manager></Manager>", text)
    elif name == "xl/workbook.xml":
        text = re.sub(
            r"<mc:AlternateContent\b[^>]*>\s*"
            r"<mc:Choice\b[^>]*>\s*"
            r"<x15ac:absPath\b[^>]*/>\s*"
            r"</mc:Choice>\s*"
            r"</mc:AlternateContent>",
            "",
            text,
        )
        text = re.sub(r"<x15ac:absPath\b[^>]*/>", "", text)

    return text, text != original


def sanitize_xlsx(path):
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    changed = []
    fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd)

    try:
        with zipfile.ZipFile(path, "r") as src, zipfile.ZipFile(tmp_path, "w") as dst:
            for item in src.infolist():
                data = src.read(item.filename)

                if item.filename in XML_TARGETS:
                    text = data.decode("utf-8")
                    text, did_change = sanitize_xml(item.filename, text)
                    data = text.encode("utf-8")
                    if did_change:
                        changed.append(item.filename)

                dst.writestr(item, data)

        if changed:
            shutil.move(tmp_path, path)
        else:
            os.remove(tmp_path)

    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    return changed


def element_text(root, path, ns):
    element = root.find(path, ns)
    return "" if element is None or element.text is None else element.text.strip()


def check_xlsx(path):
    issues = []

    with zipfile.ZipFile(path, "r") as zf:
        core_xml = zf.read("docProps/core.xml").decode("utf-8")
        core_root = ET.fromstring(core_xml)
        if element_text(core_root, "dc:creator", CORE_NS):
            issues.append("docProps/core.xml: creator is not empty")
        if element_text(core_root, "cp:lastModifiedBy", CORE_NS):
            issues.append("docProps/core.xml: lastModifiedBy is not empty")

        app_entry = zf.getinfo("docProps/app.xml") if "docProps/app.xml" in zf.namelist() else None
        if app_entry:
            app_xml = zf.read(app_entry.filename).decode("utf-8")
            app_root = ET.fromstring(app_xml)
            if element_text(app_root, "ep:Company", APP_NS):
                issues.append("docProps/app.xml: Company is not empty")
            if element_text(app_root, "ep:Manager", APP_NS):
                issues.append("docProps/app.xml: Manager is not empty")

        for item in zf.infolist():
            if item.file_size > 5_000_000:
                continue
            try:
                text = zf.read(item.filename).decode("utf-8")
            except UnicodeDecodeError:
                continue
            if LOCAL_PATH_PATTERNS.search(text):
                issues.append(f"{item.filename}: local path marker remains")

    return issues


def main():
    parser = argparse.ArgumentParser(description="Remove local/private Excel metadata from xlsx files.")
    parser.add_argument("xlsx", nargs="+", help="xlsx file(s) to sanitize")
    parser.add_argument("--check", action="store_true", help="fail if private metadata remains")
    args = parser.parse_args()

    failed = False
    for xlsx in args.xlsx:
        changed = sanitize_xlsx(xlsx)
        issues = check_xlsx(xlsx)
        if changed:
            print(f"sanitized: {xlsx} ({', '.join(changed)})")
        else:
            print(f"already clean: {xlsx}")

        if issues:
            failed = True
            for issue in issues:
                print(f"private metadata still present in {xlsx}: {issue}", file=sys.stderr)

    if failed or args.check:
        sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
