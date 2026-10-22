"""HTTP contracts exercise real PostgreSQL under the restricted application login."""
import os
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    if not os.getenv('PGDATABASE','accessledger_test').startswith('accessledger_test'):
        raise RuntimeError('API tests require disposable test database')
    return TestClient(app)


def test_database_dashboard_and_pagination(client):
    r=client.get('/api/v1/reports/dashboard');assert r.status_code==200
    assert r.json()['total_users']>=20
    r=client.get('/api/v1/users?limit=2&offset=1');assert r.status_code==200
    assert len(r.json()['items'])==2 and r.json()['total']>=20


def test_five_connected_operations(client):
    token=uuid4().hex[:10]
    dep=client.post('/api/v1/departments',json={'department_name':'API '+token}); assert dep.status_code==201
    u=client.post('/api/v1/users',json={'full_name':'API Employee','email':token+'@example.com','department_id':dep.json()['department_id']});assert u.status_code==201
    uid=u.json()['user_id']
    role=client.post('/api/v1/roles',json={'role_name':'API Role '+token});assert role.status_code==201
    rid=role.json()['role_id']
    resource=client.post('/api/v1/resources',json={'resource_code':token,'name':'API Database','type':'DATABASE'});assert resource.status_code==201
    res=resource.json()['resource_id']
    perm=client.post('/api/v1/permissions',json={'resource_id':res,'action_code':'READ'});assert perm.status_code==201
    pid=perm.json()['permission_id']
    assert client.post(f'/api/v1/users/{uid}/roles/{rid}').status_code==201
    assert client.post(f'/api/v1/roles/{rid}/permissions/{pid}').status_code==201
    assert client.post(f'/api/v1/users/{uid}/roles/{rid}').status_code==409
    assert client.get(f'/api/v1/users/{uid}/effective-permissions').json()['items'][0]['permission_id']==pid
    result=client.post('/api/v1/evaluations',json={'user_id':uid,'permission_id':pid});assert result.status_code==200
    assert result.json()['decision']=='ALLOW' and result.json()['log_id']
    assert client.delete(f'/api/v1/users/{uid}/roles/{rid}').status_code==204
    result=client.post('/api/v1/evaluations',json={'user_id':uid,'permission_id':pid});assert result.json()['decision']=='DENY'
    logs=client.get(f'/api/v1/audit?user_id={uid}&resource_id={res}').json()
    assert logs['total']==2 and {x['decision'] for x in logs['items']}=={'ALLOW','DENY'}
    assert client.get(f'/api/v1/audit?user_id={uid}&decision=DENY').json()['total']==1
    assert client.get('/api/v1/audit?search='+token).json()['total']==2
    assert client.patch(f'/api/v1/users/{uid}',json={'full_name':'Renamed','email':token+'@example.com','department_id':dep.json()['department_id']}).json()['full_name']=='Renamed'
    assert client.patch(f'/api/v1/roles/{rid}',json={'is_active':False}).json()['is_active'] is False
    assert client.patch(f'/api/v1/resources/{res}',json={'is_active':False}).json()['is_active'] is False
    assert client.patch(f'/api/v1/users/{uid}/status',json={'status':'DISABLED'}).json()['status']=='DISABLED'


@pytest.mark.parametrize('path,payload',[
    ('/users',{'full_name':'','email':'bad','department_id':1}),
    ('/evaluations',{'user_id':1,'permission_id':1,'decision':'ALLOW'}),
    ('/permissions',{'resource_id':1,'action_code':''})])
def test_validation_rejects_invalid_and_extra_inputs(client,path,payload):
    assert client.post('/api/v1'+path,json=payload).status_code==422


def test_invalid_references_and_date_validation(client):
    n=client.get('/api/v1/audit').json()['total']
    r=client.post('/api/v1/evaluations',json={'user_id':999999,'permission_id':1})
    assert r.status_code==404 and r.json()['decision']=='DENY' and r.json()['log_id'] is None
    assert client.get('/api/v1/audit').json()['total']==n
    assert client.get('/api/v1/audit?date_from=2026-01-01T00:00:00').status_code==422
    assert client.get('/api/v1/audit?date_from=2027-01-01T00:00:00Z&date_to=2026-01-01T00:00:00Z').status_code==422
    assert client.get('/api/v1/users?limit=0').status_code==422
    assert client.patch('/api/v1/roles/999999',json={'is_active':False}).status_code==404


def test_failed_commit_does_not_return_allow(client):
    from tests.database.test_engine import connect
    with connect() as c:
        c.execute("CREATE FUNCTION test_commit_failure() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'injected commit failure'; END $$")
        c.execute('CREATE CONSTRAINT TRIGGER test_deferred_audit_failure AFTER INSERT ON access_log DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION test_commit_failure()')
        before=c.execute('SELECT count(*) n FROM access_log').fetchone()['n']
        uid=c.execute("SELECT user_id FROM app_user WHERE email='priya.sharma@uni.edu'").fetchone()['user_id']
        pid=c.execute("SELECT permission_id FROM permission p JOIN resource r USING(resource_id) WHERE resource_code='RES-DB-01' AND action_code='READ'").fetchone()['permission_id']
    try:
        result=client.post('/api/v1/evaluations',json={'user_id':uid,'permission_id':pid})
        assert result.status_code==500 and 'decision' not in result.json()
        with connect() as c:
            assert c.execute('SELECT count(*) n FROM access_log').fetchone()['n']==before
    finally:
        with connect() as c:
            c.execute('DROP TRIGGER test_deferred_audit_failure ON access_log')
            c.execute('DROP FUNCTION test_commit_failure()')


def test_database_unavailable_returns_503(client,monkeypatch):
    from sqlalchemy import create_engine
    from backend.app import db
    broken=create_engine('postgresql+psycopg://nobody@127.0.0.1:1/accessledger_test',connect_args={'connect_timeout':1})
    monkeypatch.setattr(db,'engine',broken)
    assert client.get('/api/v1/reports/dashboard').status_code==503
    broken.dispose()


def test_filtered_date_range_and_aggregate_match(client):
    query='user_id=1&date_from=2000-01-01T00:00:00Z&date_to=2100-01-01T00:00:00Z'
    logs=client.get('/api/v1/audit?'+query).json()
    summary=client.get('/api/v1/reports/audit-summary?'+query).json()
    assert logs['total']==summary['total_events']==summary['allow_count']+summary['deny_count']
    assert client.get('/api/v1/reports/activity?limit=1').json()['items'][0]['total_attempts']>=0
    assert client.get('/api/v1/reports/users-without-permissions').status_code==200
    assert client.get('/api/v1/reports/sensitive-permissions').status_code==200
