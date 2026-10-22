#!/usr/bin/env python3
"""Create without resetting; migrate and seed only when empty."""
import os
import subprocess
from pathlib import Path
import psycopg
from psycopg import sql
from dotenv import load_dotenv
load_dotenv()
root=Path(__file__).resolve().parents[1]
name=os.getenv('PGDATABASE','accessledger_demo')
if name != 'accessledger_demo' and not name.startswith(('accessledger_test','accessledger_bench')):
    raise SystemExit('Refusing to target the preserved database')
kw=dict(host=os.getenv('PGHOST',str(root/'.pgsock')),port=os.getenv('PGPORT','55432'),
        user=os.getenv('PGUSER','postgres'),password=os.getenv('PGPASSWORD'))
with psycopg.connect(**kw,dbname='postgres',autocommit=True) as conn:
    if not conn.execute('SELECT 1 FROM pg_database WHERE datname=%s',(name,)).fetchone():
        conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
subprocess.run([str(root/'.venv/bin/alembic'),'-c',str(root/'alembic.ini'),'upgrade','head'],cwd=root,
               env={**os.environ,'PGDATABASE':name},check=True)
with psycopg.connect(**kw,dbname=name) as conn:
    conn.execute(sql.SQL('ALTER ROLE accessledger_demo_app PASSWORD {}').format(
        sql.Literal(os.getenv('APP_DB_PASSWORD','local-demo-only'))))
    if not conn.execute('SELECT EXISTS(SELECT 1 FROM department)').fetchone()[0]:
        conn.execute((root/'database/seed/020_complete_demo.sql').read_text())
print(f'{name}: migrated; existing data preserved')
