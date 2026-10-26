from recommender.data import time_based_split
from recommender.evaluate import precision_recall_at_k
from recommender.models import PopularityRecommender, SVDRecommender
from tests.data_utils import synthetic_ratings


def test_time_split_holds_out_each_users_latest_ratings():
    train, test = time_based_split(synthetic_ratings())
    assert len(test) > 0
    for user, t in test.groupby("userId"):
        assert t["timestamp"].min() > train.loc[train.userId == user, "timestamp"].max()


def test_popularity_skips_seen_movies():
    ratings = synthetic_ratings()
    model = PopularityRecommender().fit(ratings)
    seen = set(ratings.loc[ratings.userId == 1, "movieId"])
    recs = model.recommend(1, 10)
    assert len(recs) == 10 and not seen & set(recs)


def test_svd_recommends_k_unseen_movies():
    ratings = synthetic_ratings()
    model = SVDRecommender(n_factors=8).fit(ratings)
    seen = set(ratings.loc[ratings.userId == 2, "movieId"])
    recs = model.recommend(2, 10)
    assert len(recs) == 10 and len(set(recs)) == 10 and not seen & set(recs)


def test_svd_cold_start_falls_back_to_popularity():
    model = SVDRecommender(n_factors=8).fit(synthetic_ratings())
    assert model.recommend(999_999, 5) == [int(m) for m in model.popularity[:5]]


def test_similar_excludes_the_movie_itself():
    model = SVDRecommender(n_factors=8).fit(synthetic_ratings())
    sims = model.similar(1, 5)
    assert len(sims) == 5 and 1 not in sims
    assert model.similar(10_000, 5) == []


def test_save_and_load_give_identical_recommendations(tmp_path):
    model = SVDRecommender(n_factors=8).fit(synthetic_ratings())
    model.save(tmp_path / "m.npz")
    loaded = SVDRecommender.load(tmp_path / "m.npz")
    assert loaded.recommend(3, 10) == model.recommend(3, 10)
    assert loaded.similar(4, 5) == model.similar(4, 5)


def test_svd_beats_popularity_when_tastes_differ():
    train, test = time_based_split(synthetic_ratings(n_users=120, per_user=30))
    pop = precision_recall_at_k(PopularityRecommender().fit(train), test, k=5)["precision_at_k"]
    svd = precision_recall_at_k(SVDRecommender(n_factors=4).fit(train), test, k=5)["precision_at_k"]
    assert 0.0 <= pop <= 1.0 and svd > pop
