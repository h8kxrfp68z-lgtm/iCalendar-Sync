.PHONY: test install lint clean help setup

help:
	@echo "iCalendar Sync - Available commands:"
	@echo ""
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make test-cov      - Run tests with coverage"
	@echo "  make lint          - Run linters"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make setup         - Interactive setup"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src/icalendar_sync --cov-report=html --cov-report=term

lint:
	black src/ tests/
	flake8 src/ tests/ --max-line-length=100

clean:
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov .coverage

setup:
	python -c "from src.icalendar_sync.calendar import cmd_setup; cmd_setup(None)"