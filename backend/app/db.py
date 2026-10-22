"""SQLAlchemy is the connectivity layer; versioned PostgreSQL SQL owns the schema."""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
load_dotenv()
ROOT=Path(__file__).resolve().parents[2]
url=os.getenv('DATABASE_URL') or URL.create('postgresql+psycopg',
    username=os.getenv('APP_DB_USER','accessledger_demo_app'),
    password=os.getenv('APP_DB_PASSWORD','local-demo-only'),
    host=os.getenv('PGHOST',str(ROOT/'.pgsock')),port=int(os.getenv('PGPORT','55432')),
    database=os.getenv('PGDATABASE','accessledger_demo'))
engine=create_engine(url,pool_pre_ping=True,pool_size=5,max_overflow=5,
                     isolation_level='READ COMMITTED',connect_args={'connect_timeout':5,
                     'options':'-c statement_timeout=15000 -c lock_timeout=10000'})


def one(statement,params=None):
    with engine.connect() as c:
        return dict(c.execute(text(statement),params or {}).mappings().one())


def mutate(statement,params=None,read=None):
    """The context commits before this function returns to an HTTP handler."""
    with engine.begin() as c:
        result=c.execute(text(statement),params or {})
        row=dict(result.mappings().one()) if result.returns_rows else None
        if read:
            query,read_params=read
            row=dict(c.execute(text(query),read_params).mappings().one())
    return row


def page(query,params,limit,offset):
    with engine.connect() as c:
        total=c.execute(text('SELECT count(*) FROM ('+query+') q'),params).scalar_one()
        items=[dict(r) for r in c.execute(text(query+' LIMIT :limit OFFSET :offset'),
                    {**params,'limit':limit,'offset':offset}).mappings()]
        return dict(items=items,total=total,limit=limit,offset=offset)
