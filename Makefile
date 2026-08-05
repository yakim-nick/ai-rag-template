.PHONY: install install-ui run ui test docker lint

install:
	pip install -r requirements.txt

install-ui:
	pip install streamlit

run:
	uvicorn app:app --reload --port 8000

ui:
	streamlit run ui/app.py

test:
	pytest tests/ -v

docker:
	docker compose up --build

lint:
	ruff check .
