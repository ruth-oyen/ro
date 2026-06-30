import argparse
import os
import sys

import pythoncom
import win32api
import win32com.client
import win32con
import win32process


ACCESS_COUNTER_MARKER = "{{ACCESS_COUNTER}}"


def excel_pid(excel):
    _, pid = win32process.GetWindowThreadProcessId(excel.Hwnd)
    return pid


def terminate_process(pid):
    handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, pid)
    try:
        win32api.TerminateProcess(handle, 0)
    finally:
        win32api.CloseHandle(handle)


def move_access_counter_marker_to_cell(workbook):
    marker_count = 0

    for worksheet in workbook.Worksheets:
        for shape_index in range(worksheet.Shapes.Count, 0, -1):
            shape = worksheet.Shapes.Item(shape_index)
            try:
                shape_text = shape.TextFrame2.TextRange.Text.strip()
            except Exception:
                continue

            if shape_text != ACCESS_COUNTER_MARKER:
                continue

            marker_cell = shape.TopLeftCell
            if marker_cell.Value not in (None, "", ACCESS_COUNTER_MARKER):
                raise ValueError(
                    "The cell under the access counter marker must be empty"
                )

            center_x_pt = shape.Left - marker_cell.Left + (shape.Width / 2)
            center_y_pt = shape.Top - marker_cell.Top + (shape.Height / 2)
            marker_cell.Value = (
                "{{ACCESS_COUNTER:"
                f"{center_x_pt:.3f}:{center_y_pt:.3f}"
                "}}"
            )
            shape.Delete()
            marker_count += 1

    if marker_count != 1:
        raise ValueError(
            "Exactly one {{ACCESS_COUNTER}} text box is required"
        )


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
        move_access_counter_marker_to_cell(wb)
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
