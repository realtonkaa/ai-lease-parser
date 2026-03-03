.PHONY: install test test-cov lint clean run-app help

help:
	@echo "Available commands:"
	@echo "  make install    Install dependencies"
	@echo "  make test       Run all tests"
	@echo "  make test-cov   Run tests with coverage report"
	@echo "  make lint       Run code style checks"
	@echo "  make clean      Remove build artifacts and cache"
	@echo "  make run-app    Launch the Streamlit web UI"

install:
	pip install -r requirements.txt

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	python -m py_compile src/*.py app/*.py
	@echo "Syntax check passed."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ .coverage htmlcov/ dist/ build/ *.egg-info/

run-app:
	streamlit run app/app.py

demo:
	python -m src.cli tests/fixtures/sample_lease_1.txt --output results.csv --quiet
	@echo "Output written to results.csv"
