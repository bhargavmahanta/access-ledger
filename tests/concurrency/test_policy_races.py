"""Two-connection concurrency tests use lock observations, never timing guesses."""
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4
import pytest
from tests.database.test_engine import connect, evaluate


def committed_policy():
    token=uuid4().hex
    with connect() as c:
        u=c.execute("INSERT INTO app_user(department_id,full_name,email) VALUES(1,'Race',%s) RETURNING user_id",(token+'@test.example',)).fetchone()['user_id']
        r=c.execute('INSERT INTO role(role_name) VALUES(%s) RETURNING role_id',(token,)).fetchone()['role_id']
        s=c.execute("INSERT INTO resource(resource_code,name,type) VALUES(%s,'Race','DATABASE') RETURNING resource_id",(token,)).fetchone()['resource_id']
        p=c.execute("INSERT INTO permission(resource_id,action_code) VALUES(%s,'READ') RETURNING permission_id",(s,)).fetchone()['permission_id']
        c.execute('CALL assign_user_role(%s,%s)',(u,r)); c.execute('CALL grant_role_permission(%s,%s)',(r,p))
    return u,r,s,p


def wait_blocked(pid):
    deadline=time.monotonic()+8
    with connect(autocommit=True) as observer:
        while time.monotonic()<deadline:
            row=observer.execute("SELECT wait_event FROM pg_stat_activity WHERE pid=%s",(pid,)).fetchone()
            if row and row['wait_event']=='advisory': return
            time.sleep(.01)
    raise AssertionError('Expected transaction did not wait for advisory policy lock')


@pytest.mark.parametrize('kind',['revoke','role','grant','user','resource'])
@pytest.mark.parametrize('writer_first',[False,True])
def test_policy_mutation_and_evaluation_are_serialized(kind,writer_first):
    u,r,s,p=committed_policy()
    stmt,args={
      'revoke':('CALL revoke_user_role(%s,%s)',(u,r)),
      'role':('CALL set_role_active(%s,false)',(r,)),
      'grant':('CALL revoke_role_permission(%s,%s)',(r,p)),
      'user':("CALL set_user_status(%s,'DISABLED')",(u,)),
      'resource':('CALL set_resource_active(%s,false)',(s,))}[kind]
    with connect(user='accessledger_demo_app') as first, connect(user='accessledger_demo_app') as second, ThreadPoolExecutor() as pool:
        pid=second.info.backend_pid
        if writer_first:
            first.execute(stmt,args)
            future=pool.submit(evaluate,second,u,p)
            wait_blocked(pid); first.commit()
            assert future.result(timeout=8)['decision']=='DENY'
            second.commit()
        else:
            original=evaluate(first,u,p); assert original['decision']=='ALLOW'
            future=pool.submit(second.execute,stmt,args)
            wait_blocked(pid); first.commit()
            future.result(timeout=8);second.commit()
            assert evaluate(first,u,p)['decision']=='DENY';first.commit()
    with connect() as c:
        rows=c.execute('SELECT decision FROM access_log WHERE user_id=%s ORDER BY log_id',(u,)).fetchall()
        assert [x['decision'] for x in rows]==(['DENY'] if writer_first else ['ALLOW','DENY'])


def test_multiple_evaluations_share_the_lock_and_commit_separate_events():
    u,r,s,p=committed_policy();barrier=Barrier(2)
    def worker():
        with connect(user='accessledger_demo_app') as c:
            result=evaluate(c,u,p)
            barrier.wait(timeout=8)  # Both must acquire shared locks before either commits.
            return result
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(worker) for _ in range(2)]
        result=[f.result(timeout=12) for f in futures]
    assert all(x['decision']=='ALLOW' for x in result)
    assert len({x['log_id'] for x in result})==2
    with connect() as c:
        assert c.execute('SELECT count(*) n FROM access_log WHERE user_id=%s',(u,)).fetchone()['n']==2
