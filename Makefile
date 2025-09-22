.PHONY: format lint selftest
format:
\tblack .
lint:
\tblack --check .
selftest:
\tpython3 unified_gui_layout.py selftest
