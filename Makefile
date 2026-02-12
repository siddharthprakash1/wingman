.PHONY: install dev test onboard agent gateway doctor clean

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

onboard:
	python -m src.main onboard

agent:
	python -m src.main agent --interactive

gateway:
	python -m src.main gateway

doctor:
	python -m src.main doctor

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
