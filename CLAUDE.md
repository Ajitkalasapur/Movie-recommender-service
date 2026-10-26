# Project notes for Claude Code

Movie recommendation service: MovieLens data, SVD collaborative filtering, FastAPI, Redis cache,
Nginx load balancing across replicas, Locust load tests, pytest, and a React front end.

## Commands (run from the project root, with the virtual environment active)
- Install: `pip install -r requirements.txt`
- Download data: `python data/download_movielens.py`
- Train and evaluate: `python -m recommender.train`
- Tests: `pytest -q`
- API alone: `uvicorn api.main:app --reload`
- Scaled stack: `docker compose up --build -d` (needs `artifacts/` from training first)
- Load tests: see README, then `python loadtest/summarize.py`

## Conventions
- Keep all tests passing; tests use synthetic data and must not need the real dataset.
- Never commit `data/ml-latest-small/`, `artifacts/`, or Locust CSV files.
- Evaluation must stay honest: choose settings on validation data only, never on the test set.
- Report real measured numbers in README results; do not invent results.
