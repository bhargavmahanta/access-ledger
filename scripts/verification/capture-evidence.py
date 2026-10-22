#!/usr/bin/env python3
"""Generate SQL output, connected scenario and live-catalog ER artifact."""
import json,os,subprocess,html
from pathlib import Path
from datetime import datetime,timezone
import psycopg
from psycopg.rows import dict_row
root=Path(__file__).resolve().parents[2]
from dotenv import load_dotenv
load_dotenv(root/'.env')
out=root/'docs/evidence/current';out.mkdir(parents=True,exist_ok=True)
name='accessledger_test_evidence'
env={**os.environ,'PGDATABASE':name,'LD_LIBRARY_PATH':str(root/'.tools/postgres/usr/lib/x86_64-linux-gnu')+(':'+os.environ['LD_LIBRARY_PATH'] if os.getenv('LD_LIBRARY_PATH') else '')}
subprocess.run([str(root/'scripts/reset-db.sh')],env=env,cwd=root,check=True)
kw=dict(host=os.getenv('PGHOST',str(root/'.pgsock')),port=os.getenv('PGPORT','55432'),user=os.getenv('PGUSER','postgres'),password=os.getenv('PGPASSWORD'),dbname=name,row_factory=dict_row)
with psycopg.connect(**kw) as c:
    tables=['department','app_user','role','user_role','resource','permission','role_permission','access_log']
    from psycopg import sql
    counts={table:c.execute(sql.SQL('SELECT count(*) n FROM {}').format(sql.Identifier(table))).fetchone()['n'] for table in tables}
    catalog=c.execute("SELECT table_name,column_name,data_type,is_nullable,column_default,is_generated FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position").fetchall()
    routines=c.execute("SELECT routine_name,routine_type FROM information_schema.routines WHERE routine_schema='public' ORDER BY routine_name").fetchall()
    facts={'captured_utc':datetime.now(timezone.utc).isoformat(),'database':name,'server':c.execute('SELECT version() v').fetchone()['v'],'seed_counts':counts,'columns':catalog,'routines':routines}
(out/'database-facts.json').write_text(json.dumps(facts,indent=2,default=str))
pgbin=root/'.tools/postgres/usr/lib/postgresql/16/bin'
psql=str(pgbin/'psql') if (pgbin/'psql').exists() else 'psql'
with (out/'sql-output.txt').open('w') as stream:
    stream.write(f"Executed UTC: {facts['captured_utc']}\nDatabase: {name}\nServer: {facts['server']}\nSeed counts: {json.dumps(counts)}\n\n");stream.flush()
    for source in sorted((root/'database/queries').glob('*.sql')):
        stream.write('\nSOURCE: '+str(source.relative_to(root))+'\n');stream.flush()
        subprocess.run([psql,'-X','-v','ON_ERROR_STOP=1','-h',kw['host'],'-p',kw['port'],'-U',kw['user'],'-d',name,'-f',str(source)],env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
    subprocess.run([psql,'-X','-v','ON_ERROR_STOP=1','-h',kw['host'],'-p',kw['port'],'-U',kw['user'],'-d',name,'-c','SELECT * FROM generate_access_activity_summary();','-c',"SELECT routine_name,routine_type FROM information_schema.routines WHERE routine_schema='public' ORDER BY routine_name;"],env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
with psycopg.connect(**{**kw,'user':'accessledger_demo_app','password':os.getenv('APP_DB_PASSWORD','local-demo-only')}) as c:
    dept=c.execute("SELECT department_id FROM department WHERE department_name='Computer Science'").fetchone()['department_id']
    user=c.execute("SELECT create_user(%s,'Demonstration Employee','submission.demo@example.com') id",(dept,)).fetchone()['id']
    role=c.execute("SELECT create_role('Submission Demonstration Role') id").fetchone()['id']
    perm=c.execute("SELECT permission_id FROM permission JOIN resource USING(resource_id) WHERE resource_code='RES-DB-01' AND action_code='READ'").fetchone()['permission_id']
    c.execute('CALL assign_user_role(%s,%s)',(user,role));c.commit()
    before_grant=c.execute('SELECT * FROM get_effective_permissions(%s)',(user,)).fetchall()
    c.execute('CALL grant_role_permission(%s,%s)',(role,perm));c.commit()
    after_grant=c.execute('SELECT * FROM get_effective_permissions(%s)',(user,)).fetchall()
    allowed=c.execute('SELECT * FROM evaluate_access(%s,%s)',(user,perm)).fetchone();c.commit()
    c.execute('CALL revoke_user_role(%s,%s)',(user,role));c.commit()
    denied=c.execute('SELECT * FROM evaluate_access(%s,%s)',(user,perm)).fetchone();c.commit()
    history=c.execute('SELECT * FROM vw_access_audit_history WHERE user_id=%s ORDER BY log_id',(user,)).fetchall()
    assert allowed['decision']=='ALLOW' and denied['decision']=='DENY'
    assert len(history)==2 and not before_grant and len(after_grant)==1
    result={'captured_utc':datetime.now(timezone.utc).isoformat(),'database':name,'actual_login':'accessledger_demo_app',
      'employee_registration':{'user_id':user,'department_id':dept},'role_assignment':{'user_id':user,'role_id':role},
      'permission_assignment':{'role_id':role,'permission_id':perm,'effective_before':before_grant,'effective_after':after_grant},
      'evaluation_before_revocation':allowed,'evaluation_after_revocation':denied,'retained_history':history}
(out/'demonstrations.json').write_text(json.dumps(result,indent=2,default=str))
# Diagram exports actual live table columns. The relation cardinalities follow required FKs.
positions={'department':(35,35),'role':(420,35),'resource':(805,35),'app_user':(35,285),'user_role':(420,285),'permission':(805,285),'access_log':(35,610),'role_permission':(420,610)}
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1000" viewBox="0 0 1120 1000"><rect width="1120" height="1000" fill="white"/>',
'<defs><marker id="one" markerWidth="18" markerHeight="22" refX="1" refY="11" orient="auto"><path d="M3 2V20 M9 2V20" stroke="#41658d" fill="none" stroke-width="1.6"/></marker><marker id="many" markerWidth="28" markerHeight="24" refX="27" refY="12" orient="auto"><circle cx="6" cy="12" r="4" fill="white" stroke="#41658d" stroke-width="1.5"/><path d="M15 12L27 2 M15 12L27 22 M15 12H27" stroke="#41658d" fill="none" stroke-width="1.6"/></marker></defs>']
# Edges are drawn first so boxes mask any paths passing beneath them.
edges=[('M165 245V285','employs',175,266),('M295 395H420','has roles',327,382),('M550 245V285','is assigned',560,266),('M935 245V285','defines',945,266),('M165 495V610','attempts',175,560),('M680 140H747V720H680','grants',750,560),('M805 395H777V720H680','belongs to',690,739),('M935 495V880H165V820','evaluates',700,900)]
for path,label,x,y in edges:svg.append(f'<path d="{path}" fill="none" stroke="#41658d" stroke-width="1.5" marker-start="url(#one)" marker-end="url(#many)"/><text x="{x}" y="{y}" fill="#60768e" font-family="Arial" font-size="11">{label}</text>')
keys={'department':['department_id'],'app_user':['user_id'],'role':['role_id'],'user_role':['user_id','role_id'],'resource':['resource_id'],'permission':['permission_id'],'role_permission':['role_id','permission_id'],'access_log':['log_id']}
fks={'app_user':['department_id'],'user_role':['user_id','role_id'],'permission':['resource_id'],'role_permission':['role_id','permission_id'],'access_log':['user_id','permission_id']}
for table,(x,y) in positions.items():
    svg.append(f'<rect x="{x}" y="{y}" width="260" height="210" rx="6" fill="#fbfcfe" stroke="#c9d5e5"/><path d="M{x+6} {y}H{x+254}Q{x+260} {y} {x+260} {y+6}V{y+37}H{x}V{y+6}Q{x} {y} {x+6} {y}" fill="#18304f"/><text x="{x+14}" y="{y+24}" fill="white" font-family="Arial" font-weight="bold" font-size="13">{table.upper()}</text>')
    columns=[row['column_name'] for row in catalog if row['table_name']==table]
    for i,column in enumerate(columns):
        tags=('PK ' if column in keys[table] else '')+('FK' if column in fks.get(table,[]) else '')
        svg.append(f'<text x="{x+13}" y="{y+61+i*21}" fill="#294566" font-family="Consolas,monospace" font-size="11">{html.escape(column)}</text><text x="{x+215}" y="{y+61+i*21}" fill="#2b6caa" font-family="Arial" font-size="9">{tags}</text>')
svg.append('<text x="35" y="955" font-family="Arial" fill="#18304f" font-size="14" font-weight="bold">AccessLedger — eight core relations</text><text x="35" y="978" font-family="Arial" fill="#71859f" font-size="11">Crow’s Foot: double bar = exactly one; circle + fork = zero or many. All child FKs are required. Full candidate keys: relational-schema.md.</text></svg>')
(root/'docs/er-diagram.svg').write_text('\n'.join(svg))
print('Captured seed counts:',counts)
print('Verified controlled scenario:',allowed['decision'],'→ revoke →',denied['decision'])
