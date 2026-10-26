"""Recommendation models: a popularity baseline and SVD collaborative filtering."""
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD


class PopularityRecommender:
    """Baseline: recommend the most-liked movies the user hasn't rated yet."""

    def __init__(self, like_threshold: float = 4.0):
        self.like_threshold = like_threshold

    def fit(self, ratings: pd.DataFrame):
        liked = ratings.loc[ratings["rating"] >= self.like_threshold, "movieId"].value_counts()
        overall = ratings["movieId"].value_counts()
        rest = [m for m in overall.index if m not in liked.index]
        self.ranking = np.array(list(liked.index) + rest, dtype=np.int64)
        self.seen = ratings.groupby("userId")["movieId"].apply(lambda s: set(s.tolist())).to_dict()
        return self

    def recommend(self, user_id: int, k: int = 10):
        seen = self.seen.get(user_id, set())
        out = []
        for m in self.ranking:
            if m not in seen:
                out.append(int(m))
                if len(out) == k:
                    break
        return out


class SVDRecommender:
    """Collaborative filtering: truncated SVD of the user-movie rating matrix (PureSVD-style).

    Scores every movie for a user from learned user and movie factors, skips movies the user
    already rated, and falls back to popularity for users it has never seen (cold start).
    """

    def __init__(self, n_factors: int = 64, random_state: int = 42):
        self.n_factors = n_factors
        self.random_state = random_state

    def fit(self, ratings: pd.DataFrame):
        self.user_ids = np.sort(ratings["userId"].unique()).astype(np.int64)
        self.item_ids = np.sort(ratings["movieId"].unique()).astype(np.int64)
        rows = pd.Index(self.user_ids).get_indexer(ratings["userId"])
        cols = pd.Index(self.item_ids).get_indexer(ratings["movieId"])
        X = sparse.csr_matrix((ratings["rating"].to_numpy(np.float32), (rows, cols)),
                              shape=(len(self.user_ids), len(self.item_ids)))
        n_components = max(1, min(self.n_factors, min(X.shape) - 1))
        svd = TruncatedSVD(n_components=n_components, random_state=self.random_state)
        self.user_factors = svd.fit_transform(X).astype(np.float32)
        self.item_factors = svd.components_.T.astype(np.float32)
        seen = X.tocsr(copy=True)
        seen.data[:] = 1.0
        self.seen = seen
        self.popularity = PopularityRecommender().fit(ratings).ranking
        self._index()
        return self

    def _index(self):
        self._u_pos = {int(u): i for i, u in enumerate(self.user_ids)}
        self._i_pos = {int(m): i for i, m in enumerate(self.item_ids)}
        norms = np.linalg.norm(self.item_factors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self._item_unit = self.item_factors / norms

    def has_item(self, movie_id: int) -> bool:
        return int(movie_id) in self._i_pos

    @staticmethod
    def _top_k(scores: np.ndarray, k: int):
        k = min(k, int(np.isfinite(scores).sum()))
        if k <= 0:
            return np.array([], dtype=np.int64)
        top = np.argpartition(-scores, k - 1)[:k]
        return top[np.argsort(-scores[top])]

    def recommend(self, user_id: int, k: int = 10):
        pos = self._u_pos.get(int(user_id))
        if pos is None:
            return [int(m) for m in self.popularity[:k]]
        scores = self.item_factors @ self.user_factors[pos]
        seen_idx = self.seen.indices[self.seen.indptr[pos]:self.seen.indptr[pos + 1]]
        scores[seen_idx] = -np.inf
        return [int(self.item_ids[i]) for i in self._top_k(scores, k)]

    def similar(self, movie_id: int, k: int = 10):
        pos = self._i_pos.get(int(movie_id))
        if pos is None:
            return []
        sims = self._item_unit @ self._item_unit[pos]
        sims[pos] = -np.inf
        return [int(self.item_ids[i]) for i in self._top_k(sims, k)]

    def save(self, path):
        """Save plain NumPy arrays, so loading never depends on the scikit-learn version."""
        np.savez_compressed(path, user_ids=self.user_ids, item_ids=self.item_ids,
                            user_factors=self.user_factors, item_factors=self.item_factors,
                            seen_indptr=self.seen.indptr, seen_indices=self.seen.indices,
                            popularity=self.popularity, n_factors=np.array([self.n_factors]))

    @classmethod
    def load(cls, path):
        d = np.load(path)
        m = cls(n_factors=int(d["n_factors"][0]))
        m.user_ids, m.item_ids = d["user_ids"], d["item_ids"]
        m.user_factors, m.item_factors = d["user_factors"], d["item_factors"]
        indices, indptr = d["seen_indices"], d["seen_indptr"]
        m.seen = sparse.csr_matrix((np.ones(len(indices), dtype=np.float32), indices, indptr),
                                   shape=(len(m.user_ids), len(m.item_ids)))
        m.popularity = d["popularity"]
        m._index()
        return m
