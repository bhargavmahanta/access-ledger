import os
os.environ.setdefault('PGDATABASE','accessledger_test')
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1]/'.env')
if not os.environ['PGDATABASE'].startswith('accessledger_test'):
    raise RuntimeError('All tests require a disposable accessledger_test* database')
if os.getenv('DATABASE_URL'):
    from sqlalchemy.engine import make_url
    if not (make_url(os.environ['DATABASE_URL']).database or '').startswith('accessledger_test'):
        raise RuntimeError('DATABASE_URL must also target a disposable test database')
