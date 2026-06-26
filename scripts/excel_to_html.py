import argparse
import os
import sys

import pythoncom
import win32api
import win32com.client
import win32con
import win32process


def excel_pid(excel):
    _, pid = win32process.GetWindowThreadProcessId(excel.Hwnd)
    return pid


def terminate_process(pid):
    handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
    try:
        win32api.TerminateProcess(handle, 0)
    finally:
        win32api.CloseHandle(handle)


def main():
    parser = argparse.ArgumentParser(description="Convert Excel file to HTML using Excel COM interface.")
    parser.add_argument("-i", "--input", required=True, help="Input Excel file (.xlsx)")
    parser.add_argument("-o", "--output", required=True, help="Output HTML file (.html)")

    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)

    if not os.path.isfile(input_path):
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)

    # Delete the existing output first to avoid Excel overwrite prompts.
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
        except Exception as e:
            print(f"Error deleting existing output file: {e}")
            sys.exit(1)

    pythoncom.CoInitialize()

    # Use a separate Excel process so building does not close the user's open Excel windows.
    excel = win32com.client.DispatchEx("Excel.Application")
    pid = excel_pid(excel)
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = None

    try:
        excel.DefaultWebOptions.AllowPNG = True
        excel.DefaultWebOptions.PixelsPerInch = 192

        wb = excel.Workbooks.Open(input_path)
        wb.SaveAs(output_path, FileFormat=44)  # 44 = xlHtml
        wb.Close(False)
        wb = None
        print(f"Saved: {output_path}")
    except Exception as e:
        print(f"Error during conversion: {e}")
        sys.exit(1)
    finally:
        try:
            if wb is not None:
                wb.Close(False)
        except Exception:
            pass
        try:
            terminate_process(pid)
        except Exception:
            pass
        excel = None
        pythoncom.CoUninitialize()


if __name__ == "__main__":
    main()
