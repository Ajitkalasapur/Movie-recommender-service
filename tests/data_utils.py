"""Small synthetic ratings with two clear taste groups, so tests never need the real dataset."""
import numpy as np
import pandas as pd


def synthetic_ratings(n_users: int = 60, n_items: int = 50, per_user: int = 20, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows, t = [], 0
    for u in range(1, n_users + 1):
        group = u % 2
        for i in rng.choice(n_items, size=per_user, replace=False):
            liked = (i < n_items // 2) == (group == 0)
            rating = float(rng.choice([4.0, 4.5, 5.0]) if liked else rng.choice([1.0, 2.0, 2.5]))
            t += 1
            rows.append((u, int(i) + 1, rating, t))
    return pd.DataFrame(rows, columns=["userId", "movieId", "rating", "timestamp"])
