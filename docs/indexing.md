# Measured indexing results

Captured: 2026-10-22T14:13:52.705584+00:00
PostgreSQL: PostgreSQL 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit
Data volume: 100,000 real evaluated audit events.

Five warm-cache EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) executions per query and configuration. Medians below are local measurements, not service-level guarantees. The benchmark database is separate from the demo and original.

| Query | Before (ms) | After (ms) | Before / after |
|---|---:|---:|---:|
| latest_denials | 35.382 | 0.045 | 786.27× |
| user_history | 0.046 | 0.035 | 1.31× |
| effective_permissions | 0.127 | 0.120 | 1.06× |

Only the decision/time/log_id index changes between runs. The user/time and permission/time indexes already exist from the baseline, as do composite relationship PK indexes and reverse-FK indexes. Small changes in unrelated queries reflect timing/cache variation; they are not evidence that the new index helps those paths.

The latest-denial query can use the new decision/time ordering to stop after 50 matching events instead of scanning/filtering and sorting the audit stream. Inspect benchmark.json for actual chosen nodes, buffer counts, planning times and all executions. The effective-permission seed is small, so sequential scans may correctly be cheaper than indexes.

EXPLAIN ANALYZE executes queries and adds instrumentation overhead. These are read-only benchmark queries. The 100,000 requests are deterministic in user/permission selection; timestamps and measured timings are genuine run-dependent values.
