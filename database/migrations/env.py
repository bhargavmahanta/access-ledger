"""Migration metadata is infrastructure, never a ninth domain table."""
import os
from pathlib import Path
from alembic import context
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv
load_dotenv()
root = Path(__file__).resolve().parents[2]
name = os.getenv('PGDATABASE', 'accessledger_demo')
if not (name == 'accessledger_demo' or name.startswith(('accessledger_test','accessledger_bench'))):
    raise RuntimeError('Migrations only target dedicated demo/test/benchmark databases')
url = URL.create('postgresql+psycopg',
    username=os.getenv('PGUSER','postgres'), password=os.getenv('PGPASSWORD'),
    host=os.getenv('PGHOST',str(root/'.pgsock')),port=int(os.getenv('PGPORT','55432')),database=name)
engine=create_engine(url)
with engine.begin() as connection:
    connection.exec_driver_sql('CREATE SCHEMA IF NOT EXISTS infrastructure')
    context.configure(connection=connection,version_table_schema='infrastructure', transactional_ddl=True)
    with context.begin_transaction():
        context.run_migrations()
