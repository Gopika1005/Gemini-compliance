# Simple Makefile for common development & deployment tasks
.PHONY: install run-api run-dashboard test docker-build docker-compose-up

install:
	python -m pip install -r requirements.txt

run-api:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-dashboard:
	streamlit run dashboard.py

test:
	python -m pytest -q

docker-build:
	docker build -f Dockerfile.api -t gemini-compliance-api:latest .
	docker build -f Dockerfile.dashboard -t gemini-compliance-dashboard:latest .

docker-compose-up:
	docker compose up --build
