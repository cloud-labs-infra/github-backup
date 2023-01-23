export PYTHONPATH := $(PYTHONPATH):$(PWD)/github_backup

env:
	python3 -m venv venv
	./venv/bin/pip install tox
	./venv/bin/pip install --no-cache-dir --upgrade -r requirements.txt

test: env
	./venv/bin/tox -v

help:
	./venv/bin/python github_backup/main.py -h
