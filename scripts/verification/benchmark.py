#!/usr/bin/env python3
"""Run on accessledger_bench only; capture actual plans, never predicted timings."""
import json
import os
import statistics
import subprocess
from pathlib import Path
from datetime import datetime,timezone
import psycopg
root=Path(__file__).resolve().parents[2]
from dotenv import load_dotenv
load_dotenv(root/'.env')
name='accessledger_bench'
subprocess.run([str(root/'.venv/bin/python'),str(root/'scripts/setup-db.py')],env={**os.environ,'PGDATABASE':name},cwd=root,check=True)
kw=dict(host=os.getenv('PGHOST',str(root/'.pgsock')),port=os.getenv('PGPORT','55432'),user=os.getenv('PGUSER','postgres'),password=os.getenv('PGPASSWORD'),dbname=name)
out=root/'docs/evidence/current';out.mkdir(parents=True,exist_ok=True)
with psycopg.connect(**kw,autocommit=True) as c:
    n=c.execute('SELECT count(*) FROM access_log').fetchone()[0]
    if n<100000:
        # Repeated controlled invocations, deterministic request pair sequence.
        c.execute('SELECT count(*) FROM generate_series(1,%s) g(i) CROSS JOIN LATERAL evaluate_access(((g.i-1)%%20)+1,((g.i-1)%%33)+1) e',(100000-n,))
    c.execute('ANALYZE')
    c.execute('DROP INDEX IF EXISTS ix_access_log_decision_time')
    queries={
      'latest_denials':"SELECT log_id,user_id,permission_id,occurred_at FROM access_log WHERE decision='DENY' ORDER BY occurred_at DESC,log_id DESC LIMIT 50",
      'user_history':"SELECT * FROM access_log WHERE user_id=1 ORDER BY occurred_at DESC LIMIT 50",
      'effective_permissions':"SELECT * FROM vw_effective_user_permissions WHERE user_id=3"}
    results={'generated_utc':datetime.now(timezone.utc).isoformat(),'server':c.execute('SELECT version()').fetchone()[0],
             'events':c.execute('SELECT count(*) FROM access_log').fetchone()[0],'repetitions':5,'queries':{}}
    def measure(sql):
        c.execute(sql).fetchall() # warm cache, same query before/after
        plans=[c.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+sql).fetchone()[0][0] for _ in range(5)]
        return {'median_execution_ms':statistics.median(p['Execution Time'] for p in plans),'runs':plans}
    for key,sql in queries.items():results['queries'][key]={'sql':sql,'before':measure(sql)}
    c.execute((root/'database/indexes/008_audit_decision.sql').read_text());c.execute('ANALYZE access_log')
    for key,sql in queries.items():results['queries'][key]['after']=measure(sql)
(out/'benchmark.json').write_text(json.dumps(results,indent=2))
lines=['# Measured indexing results','',f"Captured: {results['generated_utc']}",f"PostgreSQL: {results['server']}",f"Data volume: {results['events']:,} real evaluated audit events.",'',
       'Five warm-cache EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) executions per query and configuration. Medians below are local measurements, not service-level guarantees. The benchmark database is separate from the demo and original.','',
       '| Query | Before (ms) | After (ms) | Before / after |','|---|---:|---:|---:|']
for key,r in results['queries'].items():
    a=r['before']['median_execution_ms'];b=r['after']['median_execution_ms']
    lines.append(f'| {key} | {a:.3f} | {b:.3f} | {a/b:.2f}× |')
lines+=['','Only the decision/time/log_id index changes between runs. The user/time and permission/time indexes already exist from the baseline, as do composite relationship PK indexes and reverse-FK indexes. Small changes in unrelated queries reflect timing/cache variation; they are not evidence that the new index helps those paths.','',
        'The latest-denial query can use the new decision/time ordering to stop after 50 matching events instead of scanning/filtering and sorting the audit stream. Inspect benchmark.json for actual chosen nodes, buffer counts, planning times and all executions. The effective-permission seed is small, so sequential scans may correctly be cheaper than indexes.','',
        'EXPLAIN ANALYZE executes queries and adds instrumentation overhead. These are read-only benchmark queries. The 100,000 requests are deterministic in user/permission selection; timestamps and measured timings are genuine run-dependent values.']
(root/'docs/indexing.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines[:15]))
