# Model results (2026-10-25)

Data: MovieLens ml-latest-small, 100,836 ratings from 610 users.
Split: each user's most recent 20% of ratings held out for testing. A liked movie means rating 4.0 or higher.

| Model | Precision@10 | Recall@10 | Users evaluated |
|---|---|---|---|
| Popularity baseline | 0.0611 | 0.0493 | 592 |
| SVD collaborative filtering (16 factors) | 0.0860 | 0.0834 | 592 |
