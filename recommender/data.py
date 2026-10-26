"""Load MovieLens data and split it by time."""
from pathlib import Path

import numpy as np
import pandas as pd


def load_ratings(data_dir) -> pd.DataFrame:
    """Read ratings.csv with columns userId, movieId, rating, timestamp."""
    return pd.read_csv(Path(data_dir) / "ratings.csv")


def load_movies(data_dir) -> pd.DataFrame:
    """Read movies.csv with columns movieId, title, genres."""
    return pd.read_csv(Path(data_dir) / "movies.csv")


def time_based_split(ratings: pd.DataFrame, test_frac: float = 0.2, min_ratings: int = 5):
    """For each user with at least `min_ratings` ratings, put their most recent `test_frac` of ratings in test.

    This mimics production: the model learns from the past and is judged on what users rated next.
    """
    r = ratings.sort_values(["userId", "timestamp"]).reset_index(drop=True)
    counts = r.groupby("userId")["movieId"].transform("size")
    order = r.groupby("userId").cumcount()
    n_test = np.ceil(counts * test_frac).astype(int)
    is_test = (counts >= min_ratings) & (order >= counts - n_test)
    return r[~is_test].reset_index(drop=True), r[is_test].reset_index(drop=True)
