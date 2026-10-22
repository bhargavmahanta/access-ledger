import os
os.environ.setdefault('PGDATABASE','accessledger_test')
if not os.environ['PGDATABASE'].startswith('accessledger_test'):
    raise RuntimeError('All tests require a disposable accessledger_test* database')
if os.getenv('DATABASE_URL'):
    from sqlalchemy.engine import make_url
    if not (make_url(os.environ['DATABASE_URL']).database or '').startswith('accessledger_test'):
        raise RuntimeError('DATABASE_URL must also target a disposable test database')
