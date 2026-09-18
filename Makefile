PYTHON ?= python3

.PHONY: all notebook check clean

all: notebook

notebook: tokenizer.ipynb

tokenizer.ipynb: tokenizer.py tools/percent_to_ipynb.py
	$(PYTHON) tools/percent_to_ipynb.py $< $@

check:
	$(PYTHON) -m py_compile tokenizer.py tools/percent_to_ipynb.py

clean:
	rm -f tokenizer.ipynb
