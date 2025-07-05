unit-test:
	python -m pytest --ignore=tests/integration

integration-test:
	python -m pytest ./tests/integration

test:
	python -m pytest