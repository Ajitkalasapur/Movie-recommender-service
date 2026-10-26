"""Top-k ranking metrics."""
import numpy as np


def precision_recall_at_k(model, test, k: int = 10, like_threshold: float = 4.0):
    """Precision@k and Recall@k over users with at least one liked movie in the test period."""
    relevant = test[test["rating"] >= like_threshold].groupby("userId")["movieId"].apply(set)
    precisions, recalls = [], []
    for user_id, rel in relevant.items():
        recs = model.recommend(int(user_id), k)
        hits = len(set(recs) & rel)
        precisions.append(hits / k)
        recalls.append(hits / len(rel))
    if not precisions:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0, "users": 0}
    return {"precision_at_k": float(np.mean(precisions)), "recall_at_k": float(np.mean(recalls)),
            "users": len(precisions)}
