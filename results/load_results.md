# Load test results

| Scenario | Requests/s | Median (ms) | 95th percentile (ms) | Requests | Failures |
|---|---|---|---|---|---|
| A: 1 replica, no cache | 2530.6 | 75 | 99 | 151896 | 0 |
| B: 3 replicas + Redis cache | 3701.8 | 3 | 170 | 222179 | 0 |
