env:
	pip3 install tox
	pip3 install --upgrade pip
	pip3 install --no-cache-dir --upgrade -r requirements.txt

test:
	tox -v