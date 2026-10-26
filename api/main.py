"""FastAPI service for movie recommendations, with optional Redis caching."""
import json
import os
import socket
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from recommender.models import SVDRecommender

ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "artifacts"))
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "")
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "300"))
HOSTNAME = socket.gethostname()   # shows which replica answered, to demonstrate load balancing
state = {}


def _connect_cache():
    if not (CACHE_ENABLED and REDIS_URL):
        return None
    try:
        import redis
        client = redis.Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=0.5)
        client.ping()
        return client
    except Exception:
        return None   # the service still works without a cache


@asynccontextmanager
async def lifespan(app):
    state["model"] = SVDRecommender.load(ARTIFACTS_DIR / "svd_model.npz")
    movies = json.loads((ARTIFACTS_DIR / "movies.json").read_text())
    state["titles"] = {int(m["movieId"]): m["title"] for m in movies}
    state["cache"] = _connect_cache()
    yield
    state.clear()


app = FastAPI(title="Movie Recommendation Service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


def _with_titles(ids):
    return [{"movieId": i, "title": state["titles"].get(i, f"Movie {i}")} for i in ids]


def _cached(key, compute):
    cache = state.get("cache")
    if cache is not None:
        try:
            hit = cache.get(key)
            if hit is not None:
                return json.loads(hit), True
        except Exception:
            pass
    value = compute()
    if cache is not None:
        try:
            cache.setex(key, CACHE_TTL, json.dumps(value))
        except Exception:
            pass
    return value, False


@app.get("/health")
def health():
    return {"status": "ok", "served_by": HOSTNAME, "cache_connected": state.get("cache") is not None}


@app.get("/recommendations/{user_id}")
def recommendations(user_id: int, k: int = Query(10, ge=1, le=50)):
    items, cached = _cached(f"rec:{user_id}:{k}", lambda: _with_titles(state["model"].recommend(user_id, k)))
    return {"user_id": user_id, "items": items, "cached": cached, "served_by": HOSTNAME}


@app.get("/similar/{movie_id}")
def similar(movie_id: int, k: int = Query(10, ge=1, le=50)):
    if not state["model"].has_item(movie_id):
        raise HTTPException(status_code=404, detail="Unknown movie")
    items, cached = _cached(f"sim:{movie_id}:{k}", lambda: _with_titles(state["model"].similar(movie_id, k)))
    return {"movie_id": movie_id, "title": state["titles"].get(movie_id, f"Movie {movie_id}"),
            "items": items, "cached": cached, "served_by": HOSTNAME}


@app.get("/movies/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=50)):
    ql = q.lower()
    hits = [{"movieId": i, "title": t} for i, t in state["titles"].items()
            if ql in t.lower() and state["model"].has_item(i)]
    return {"items": hits[:limit]}


@app.get("/movies/popular")
def popular(n: int = Query(50, ge=1, le=500)):
    return {"items": _with_titles([int(m) for m in state["model"].popularity[:n]])}
