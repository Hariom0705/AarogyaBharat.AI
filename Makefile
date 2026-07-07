.PHONY: install playground run test clean

install:
	uv sync

playground:
	uv run adk web app --host 127.0.0.1 --port 18081 --reload_agents

run-backend:
	uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

run-frontend:
	uv run streamlit run frontend/patient_app.py --server.port 8501

test:
	uv run pytest tests/
