.PHONY : clean

index.html : src/index.xlsx
	py -3.13 scripts/sanitize_xlsx_metadata.py src/index.xlsx
	py -3.13 scripts/excel_to_html.py -i src/index.xlsx -o index.html
#	py -3.13 scripts/excel_to_html_postfix.py

clean:
	rm -f index.html
	rm -rf index.files
