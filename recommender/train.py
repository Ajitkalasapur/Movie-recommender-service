"""Train, evaluate, and save the recommender.

Run from the project root:  python -m recommender.train
"""
import argparse
import datetime
import json
from pathlib import Path

from recommender.data import load_movies, load_ratings, time_based_split
from recommender.evaluate import precision_recall_at_k
from recommender.models import PopularityRecommender, SVDRecommender


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data/ml-latest-small")
    ap.add_argument("--artifacts", default="artifacts")
    ap.add_argument("--results", default="results")
    ap.add_argument("--k", type=int, default=10)
    ap.add_argument("--factors", default="16,32,64,128", help="SVD factor counts to compare on validation data")
    args = ap.parse_args()

    ratings = load_ratings(args.data_dir)
    movies = load_movies(args.data_dir)
    train, test = time_based_split(ratings)
    sub_train, val = time_based_split(train)          # validation comes only from the training period
    print(f"{len(ratings):,} ratings | {ratings.userId.nunique()} users | {ratings.movieId.nunique():,} movies")
    print(f"train {len(train):,} | test {len(test):,} (each user's most recent 20%)")

    best_f, best_p = None, -1.0
    for f in [int(x) for x in args.factors.split(",")]:
        p = precision_recall_at_k(SVDRecommender(f).fit(sub_train), val, args.k)["precision_at_k"]
        print(f"  validation Precision@{args.k} with {f} factors: {p:.4f}")
        if p > best_p:
            best_f, best_p = f, p
    print(f"Chosen: {best_f} factors (picked on validation data, never on test)")

    rows = [("Popularity baseline", precision_recall_at_k(PopularityRecommender().fit(train), test, args.k)),
            (f"SVD collaborative filtering ({best_f} factors)",
             precision_recall_at_k(SVDRecommender(best_f).fit(train), test, args.k))]

    # The served model learns from all ratings, using the setting chosen above.
    art = Path(args.artifacts)
    art.mkdir(parents=True, exist_ok=True)
    SVDRecommender(best_f).fit(ratings).save(art / "svd_model.npz")
    (art / "movies.json").write_text(json.dumps(movies[["movieId", "title"]].to_dict("records")))

    res = Path(args.results)
    res.mkdir(parents=True, exist_ok=True)
    k = args.k
    lines = [f"# Model results ({datetime.date.today()})", "",
             f"Data: MovieLens ml-latest-small, {len(ratings):,} ratings from {ratings.userId.nunique()} users.",
             "Split: each user's most recent 20% of ratings held out for testing. A liked movie means rating 4.0 or higher.", "",
             f"| Model | Precision@{k} | Recall@{k} | Users evaluated |", "|---|---|---|---|"]
    for name, m in rows:
        lines.append(f"| {name} | {m['precision_at_k']:.4f} | {m['recall_at_k']:.4f} | {m['users']} |")
    (res / "model_results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[5:]))
    print(f"\nSaved model to {art}/ and results to {res}/model_results.md")


if __name__ == "__main__":
    main()
