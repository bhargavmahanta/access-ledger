"""Behavior of authoritative authorization and corrected aggregates."""
import os
import psycopg
import pytest
from psycopg.rows import dict_row
from pathlib import Path


def connect(user='postgres', **kw):
    name = os.environ.get('PGDATABASE', 'accessledger_test')
    if not name.startswith('accessledger_test'):
        raise RuntimeError('Tests require an accessledger_test* database')
    return psycopg.connect(host=os.getenv('PGHOST', str(Path(__file__).resolve().parents[2]/'.pgsock')),
                          port=os.getenv('PGPORT', '55432'), dbname=name,
                          user=user, row_factory=dict_row, **kw)


@pytest.fixture
def db():
    with connect() as c:
        yield c
        c.rollback()


def test_authoritative_evaluation_records_one_event(db):
    before = db.execute('SELECT count(*) n FROM access_log').fetchone()['n']
    result = db.execute("SELECT * FROM evaluate_access((SELECT user_id FROM app_user WHERE email='priya.sharma@uni.edu'), (SELECT permission_id FROM permission p JOIN resource r USING(resource_id) WHERE resource_code='RES-DB-01' AND action_code='READ'))").fetchone()
    assert result['decision'] == 'ALLOW'
    assert result['reason_code'] == 'PERMISSION_GRANTED'
    assert result['log_id'] is not None
    assert db.execute('SELECT count(*) n FROM access_log').fetchone()['n'] == before + 1


def test_resource_report_does_not_multiply_audit_events(db):
    assert db.execute('SELECT sum(attempts) n FROM vw_resource_access_summary').fetchone()['n'] == db.execute('SELECT count(*) n FROM access_log').fetchone()['n']


def test_application_cannot_forge_allow(db):
    db.execute('SET LOCAL ROLE accessledger_demo_app')
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute("INSERT INTO access_log(user_id,permission_id,reason_code) SELECT user_id,permission_id,'PERMISSION_GRANTED' FROM access_log LIMIT 1")

@pytest.fixture
def policy(db):
    u=db.execute("INSERT INTO app_user(department_id,full_name,email) VALUES(1,'Policy Test','policy-test@example.test') RETURNING user_id").fetchone()['user_id']
    r=db.execute("INSERT INTO role(role_name) VALUES('Policy Test') RETURNING role_id").fetchone()['role_id']
    s=db.execute("INSERT INTO resource(resource_code,name,type) VALUES('POLICY-TEST','Policy Test','DATABASE') RETURNING resource_id").fetchone()['resource_id']
    p=db.execute("INSERT INTO permission(resource_id,action_code) VALUES(%s,'READ') RETURNING permission_id",(s,)).fetchone()['permission_id']
    db.execute('CALL assign_user_role(%s,%s)',(u,r)); db.execute('CALL grant_role_permission(%s,%s)',(r,p))
    return u,r,s,p


def evaluate(db,u,p):
    return db.execute('SELECT * FROM evaluate_access(%s,%s)',(u,p)).fetchone()


@pytest.mark.parametrize('mutation,reason',[
    ('CALL set_user_status(%s,\'DISABLED\')','USER_DISABLED'),
    ('CALL set_resource_active(%s,false)','RESOURCE_INACTIVE'),
    ('CALL set_role_active(%s,false)','NO_ACTIVE_ROLE'),
    ('CALL revoke_role_permission(%s,%s)','PERMISSION_NOT_GRANTED'),
    ('CALL revoke_user_role(%s,%s)','NO_ACTIVE_ROLE')])
def test_policy_changes_apply_and_history_survives(db,policy,mutation,reason):
    u,r,s,p=policy
    first=evaluate(db,u,p); assert first['decision']=='ALLOW'
    args=(u,) if 'user_status' in mutation else (s,) if 'resource_active' in mutation else (r,) if 'role_active' in mutation else (r,p) if 'role_permission' in mutation else (u,r)
    db.execute(mutation,args)
    second=evaluate(db,u,p)
    assert second['decision']=='DENY' and second['reason_code']==reason
    assert db.execute('SELECT decision FROM access_log WHERE log_id=%s',(first['log_id'],)).fetchone()['decision']=='ALLOW'


def test_invalid_references_do_not_create_history(db):
    before=db.execute('SELECT count(*) n FROM access_log').fetchone()['n']
    assert evaluate(db,-1,-1)==dict(decision='DENY',reason_code='USER_NOT_FOUND',log_id=None,occurred_at=None)
    assert evaluate(db,1,-1)['reason_code']=='PERMISSION_NOT_FOUND'
    assert db.execute('SELECT count(*) n FROM access_log').fetchone()['n']==before


def test_repeated_evaluations_and_multiple_roles(db,policy):
    u,r,s,p=policy
    db.execute('CALL assign_user_role(%s,1)',(u,))
    db.execute('CALL grant_role_permission(1,%s)',(p,))
    rows=db.execute('SELECT * FROM get_effective_permissions(%s)',(u,)).fetchall()
    assert sum(x['permission_id']==p for x in rows)==1
    a=evaluate(db,u,p); b=evaluate(db,u,p)
    assert a['log_id']!=b['log_id']


def test_reason_precedence(db,policy):
    u,r,s,p=policy
    db.execute("CALL set_user_status(%s,'DISABLED')",(u,));db.execute('CALL set_resource_active(%s,false)',(s,))
    assert evaluate(db,u,p)['reason_code']=='USER_DISABLED'
    assert evaluate(db,u,-1)['reason_code']=='PERMISSION_NOT_FOUND'


def test_audit_failure_aborts_evaluation(db,policy):
    u,r,s,p=policy
    db.execute("CREATE FUNCTION fail_test_audit() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'injected audit failure'; END $$")
    db.execute('CREATE TRIGGER test_audit_failure BEFORE INSERT ON access_log FOR EACH ROW EXECUTE FUNCTION fail_test_audit()')
    n=db.execute('SELECT count(*) n FROM access_log').fetchone()['n']
    with pytest.raises(psycopg.errors.RaiseException), db.transaction():
        evaluate(db,u,p)
    assert db.execute('SELECT count(*) n FROM access_log').fetchone()['n']==n


def test_actual_app_login_and_forbidden_policy_writes():
    with connect(user='accessledger_demo_app') as c:
        assert c.execute('SELECT current_user AS u').fetchone()['u']=='accessledger_demo_app'
        uid=c.execute("SELECT user_id FROM app_user WHERE email='priya.sharma@uni.edu'").fetchone()['user_id']
        pid=c.execute("SELECT permission_id FROM permission p JOIN resource r USING(resource_id) WHERE resource_code='RES-DB-01' AND action_code='READ'").fetchone()['permission_id']
        assert evaluate(c,uid,pid)['decision']=='ALLOW'
        for statement in ["INSERT INTO access_log(user_id,permission_id,reason_code) VALUES(1,1,'PERMISSION_GRANTED')",
                          "UPDATE access_log SET reason_code='USER_DISABLED' WHERE log_id=1",
                          'DELETE FROM access_log WHERE log_id=1','TRUNCATE access_log',
                          'DELETE FROM user_role WHERE user_id=1', 'UPDATE role SET is_active=false WHERE role_id=1',
                          'UPDATE app_user SET status=\'DISABLED\' WHERE user_id=1',
                          'UPDATE resource SET is_active=false WHERE resource_id=1',
                          'DELETE FROM role_permission WHERE role_id=1']:
            with pytest.raises(psycopg.errors.InsufficientPrivilege), c.transaction():
                c.execute(statement)
        c.rollback()


def test_permission_trigger_and_cursor(db,policy):
    u,r,s,p=policy; evaluate(db,u,p)
    with pytest.raises(psycopg.errors.RestrictViolation),db.transaction():
        db.execute('CALL update_permission_identity(%s,%s,\'WRITE\')',(p,s))
    summary=db.execute('SELECT * FROM generate_access_activity_summary() WHERE user_id=%s',(u,)).fetchone()
    assert summary['total_attempts']==summary['allowed_attempts']+summary['denied_attempts']==1
    assert len(db.execute('SELECT * FROM generate_access_activity_summary()').fetchall())==db.execute('SELECT count(*) n FROM app_user').fetchone()['n']


def test_unsupported_isolation_is_rejected():
    with connect() as c:
        c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
        with pytest.raises(psycopg.errors.InvalidTransactionState): evaluate(c,1,1)
        c.rollback()


def test_schema_and_seed_counts(db):
    names=['department','app_user','role','resource','permission','user_role','role_permission','access_log']
    assert db.execute("SELECT count(*) n FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'").fetchone()['n']==8
    from psycopg import sql
    for name in names:
        assert db.execute(sql.SQL('SELECT count(*) n FROM {}').format(sql.Identifier(name))).fetchone()['n']>=10


def test_transaction_rollback_has_no_audit_event(policy,db):
    u,r,s,p=policy
    try:
        with db.transaction():
            result=evaluate(db,u,p)
            raise psycopg.Rollback
    except psycopg.Rollback:
        pass
    assert db.execute('SELECT count(*) n FROM access_log WHERE log_id=%s',(result['log_id'],)).fetchone()['n']==0
