BUILD_XLSX := .build/index.xlsx
BUILD_INPUTS := \
	scripts/counter.txt \
	scripts/prepare_build_xlsx.py \
	scripts/sanitize_xlsx_metadata.py \
	scripts/excel_to_html.py \
	scripts/excel_to_html_postfix.py

.PHONY : clean

index.html : src/index.xlsx $(BUILD_INPUTS)
	py -3.13 scripts/prepare_build_xlsx.py src/index.xlsx $(BUILD_XLSX)
	py -3.13 scripts/sanitize_xlsx_metadata.py $(BUILD_XLSX)
	py -3.13 scripts/excel_to_html.py -i $(BUILD_XLSX) -o index.html
	py -3.13 scripts/excel_to_html_postfix.py

clean:
	rm -rf .build
	rm -f index.html
	rm -rf index.files
