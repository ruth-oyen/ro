BUILD_XLSX := .build/index.xlsx

.PHONY : clean

index.html : src/index.xlsx
	py -3.13 scripts/prepare_build_xlsx.py src/index.xlsx $(BUILD_XLSX)
	py -3.13 scripts/sanitize_xlsx_metadata.py $(BUILD_XLSX)
	py -3.13 scripts/excel_to_html.py -i $(BUILD_XLSX) -o index.html
	py -3.13 scripts/excel_to_html_postfix.py

clean:
	rm -rf .build
	rm -f index.html
	rm -rf index.files
