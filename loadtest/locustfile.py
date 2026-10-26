"""Load test through Nginx. Example (headless, 60 seconds, 200 simulated users, 4 processes):

locust -f loadtest/locustfile.py --host http://localhost:8080 --users 200 --spawn-rate 50 \
       --run-time 60s --headless --processes 4 --csv results/scenario_b
"""
import random

from locust import HttpUser, constant, task


class MovieFan(HttpUser):
    wait_time = constant(0)   # no think time, so the service is the bottleneck, not the user count

    def on_start(self):
        r = self.client.get("/api/movies/popular?n=200", name="/api/movies/popular")
        self.movies = [m["movieId"] for m in r.json()["items"]] if r.ok else [1]

    @task(3)
    def recommend(self):
        self.client.get(f"/api/recommendations/{random.randint(1, 610)}?k=10", name="/api/recommendations/[user]")

    @task(1)
    def similar(self):
        self.client.get(f"/api/similar/{random.choice(self.movies)}?k=10", name="/api/similar/[movie]")
