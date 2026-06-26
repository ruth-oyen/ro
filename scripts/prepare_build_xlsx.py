import argparse
import shutil
from pathlib import Path


def copy_xlsx(source, destination):
    try:
        shutil.copyfile(source, destination)
    except PermissionError:
        copy_xlsx_shared(source, destination)


def copy_xlsx_shared(source, destination):
    import win32con
    import win32file

    share_mode = (
        win32con.FILE_SHARE_READ
        | win32con.FILE_SHARE_WRITE
        | win32con.FILE_SHARE_DELETE
    )
    source_handle = win32file.CreateFile(
        str(source),
        win32con.GENERIC_READ,
        share_mode,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_ATTRIBUTE_NORMAL,
        None,
    )

    try:
        with destination.open("wb") as output:
            while True:
                _, data = win32file.ReadFile(source_handle, 1024 * 1024)
                if not data:
                    break
                output.write(data)
    finally:
        source_handle.Close()


def main():
    parser = argparse.ArgumentParser(description="Copy an xlsx source file for build-time conversion.")
    parser.add_argument("source", help="Source .xlsx file")
    parser.add_argument("destination", help="Build copy destination")
    args = parser.parse_args()

    source = Path(args.source)
    destination = Path(args.destination)

    if not source.is_file():
        raise FileNotFoundError(source)

    destination.parent.mkdir(parents=True, exist_ok=True)
    copy_xlsx(source, destination)
    print(f"Prepared build copy: {destination}")


if __name__ == "__main__":
    main()
