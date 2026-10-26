import importlib
import json

import pytest
from fastapi.testclient import TestClient

from recommender.models import SVDRecommender
from tests.data_utils import synthetic_ratings


@pytest.fixture()
def client(tmp_path, monkeypatch):
    ratings = synthetic_ratings()
    SVDRecommender(n_factors=8).fit(ratings).save(tmp_path / "svd_model.npz")
    movies = [{"movieId": int(m), "title": f"Movie {m}"} for m in sorted(ratings.movieId.unique())]
    (tmp_path / "movies.json").write_text(json.dumps(movies))
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    monkeypatch.setenv("CACHE_ENABLED", "false")
    import api.main as main
    importlib.reload(main)
    with TestClient(main.app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_recommendations_return_titled_items(client):
    r = client.get("/recommendations/1?k=5")
    body = r.json()
    assert r.status_code == 200 and len(body["items"]) == 5
    assert all("title" in item for item in body["items"]) and body["cached"] is False


def test_unknown_user_gets_popular_movies(client):
    assert len(client.get("/recommendations/999999?k=5").json()["items"]) == 5


def test_similar_movies_and_unknown_movie(client):
    assert client.get("/similar/1?k=5").status_code == 200
    assert client.get("/similar/10000").status_code == 404


def test_search_and_popular(client):
    assert client.get("/movies/search?q=Movie 1").json()["items"]
    assert len(client.get("/movies/popular?n=10").json()["items"]) == 10


def test_k_is_validated(client):
    assert client.get("/recommendations/1?k=0").status_code == 422
