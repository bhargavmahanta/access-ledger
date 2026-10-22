"""Trusted local demo API. Authorization decisions originate only in PostgreSQL."""
import logging
import os
from typing import Annotated, Literal
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, OperationalError
from .db import engine,one,page,mutate
from .schemas import *

app=FastAPI(title='AccessLedger',version='1.0.0',description='Local academic RBAC and audit demonstration')
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://127.0.0.1:5173,http://localhost:5173').split(','),allow_methods=['GET','POST','PATCH','DELETE'],allow_headers=['Content-Type'])
log=logging.getLogger('accessledger')
Limit=Annotated[int,Query(ge=1,le=200)]
Offset=Annotated[int,Query(ge=0)]
PREFIX='/api/v1'
USERS='SELECT u.*,d.department_name FROM app_user u JOIN department d USING(department_id)'
PERMISSIONS='SELECT p.*,r.resource_code,r.name resource_name FROM permission p JOIN resource r USING(resource_id)'

@app.exception_handler(DBAPIError)
def database_error(request,exc):
    state=getattr(exc.orig,'sqlstate',None)
    if isinstance(exc,OperationalError) or (state and state.startswith('08')) or state in ('55P03','57014'):
        code,message=503,'Database unavailable or operation timed out; retry the request.'
    elif state=='P0002': code,message=404,'Requested record or assignment was not found.'
    elif state=='23503': code,message=404,'Referenced record was not found, or is still in use.'
    elif state in ('23505','23514','23001','25000'): code,message=409,'Operation conflicts with the current record or policy.'
    else:
        log.exception('Database operation failed (SQLSTATE %s)',state)
        code,message=500,'Database operation failed; no change was committed.'
    return JSONResponse(status_code=code,content={'detail':message})


def record(query,key,value):
    data=page(query+' WHERE '+key+'=:id',{'id':value},1,0)['items']
    if not data: raise HTTPException(404,'Record not found')
    return data[0]

@app.get('/health')
def health():
    return {'status':'ok','database':one('SELECT current_database() name')['name']}

@app.get(PREFIX+'/departments',response_model=Page[DepartmentOut])
def departments(limit:Limit=50,offset:Offset=0):
    return page('SELECT * FROM department ORDER BY department_id',{},limit,offset)
@app.post(PREFIX+'/departments',response_model=DepartmentOut,status_code=201)
def create_department(body:DepartmentIn):
    r=mutate('SELECT create_department(:department_name) department_id',body.model_dump())
    return record('SELECT * FROM department','department_id',r['department_id'])
@app.patch(PREFIX+'/departments/{id}',response_model=DepartmentOut)
def update_department(id:int,body:DepartmentIn):
    mutate('CALL update_department(:id,:department_name)',{'id':id,**body.model_dump()})
    return record('SELECT * FROM department','department_id',id)

@app.get(PREFIX+'/users',response_model=Page[UserOut])
def users(limit:Limit=50,offset:Offset=0,search:str=Query('',max_length=150)):
    return page(USERS+" WHERE u.full_name ILIKE :search OR u.email ILIKE :search ORDER BY u.user_id",{'search':'%'+search+'%'},limit,offset)
@app.post(PREFIX+'/users',response_model=UserOut,status_code=201)
def create_user(body:UserIn):
    r=mutate('SELECT create_user(:department_id,:full_name,:email) user_id',body.model_dump())
    return record(USERS,'u.user_id',r['user_id'])
@app.patch(PREFIX+'/users/{id}',response_model=UserOut)
def update_user(id:int,body:UserIn):
    mutate('CALL update_user(:id,:department_id,:full_name,:email)',{'id':id,**body.model_dump()})
    return record(USERS,'u.user_id',id)
@app.patch(PREFIX+'/users/{id}/status',response_model=UserOut)
def user_status(id:int,body:UserStatus):
    mutate('CALL set_user_status(:id,:status)',{'id':id,**body.model_dump()})
    return record(USERS,'u.user_id',id)
@app.get(PREFIX+'/users/{id}/roles',response_model=Page[RoleOut])
def user_roles(id:int,limit:Limit=50,offset:Offset=0):
    record(USERS,'u.user_id',id)
    return page('SELECT r.* FROM role r JOIN user_role ur USING(role_id) WHERE ur.user_id=:id ORDER BY r.role_id',{'id':id},limit,offset)
@app.get(PREFIX+'/users/{id}/effective-permissions',response_model=Page[PermissionOut])
def effective(id:int,limit:Limit=50,offset:Offset=0):
    record(USERS,'u.user_id',id)
    return page('SELECT * FROM get_effective_permissions(:id) ORDER BY permission_id',{'id':id},limit,offset)
@app.post(PREFIX+'/users/{id}/roles/{role_id}',status_code=201)
def assign(id:int,role_id:int):
    mutate('CALL assign_user_role(:id,:role)',{'id':id,'role':role_id});return {'user_id':id,'role_id':role_id}
@app.delete(PREFIX+'/users/{id}/roles/{role_id}',status_code=204)
def revoke(id:int,role_id:int):
    mutate('CALL revoke_user_role(:id,:role)',{'id':id,'role':role_id});return Response(status_code=204)

@app.get(PREFIX+'/roles',response_model=Page[RoleOut])
def roles(limit:Limit=50,offset:Offset=0): return page('SELECT * FROM role ORDER BY role_id',{},limit,offset)
@app.post(PREFIX+'/roles',response_model=RoleOut,status_code=201)
def create_role(body:RoleIn):
    r=mutate('SELECT create_role(:role_name) role_id',body.model_dump());return record('SELECT * FROM role','role_id',r['role_id'])
@app.patch(PREFIX+'/roles/{id}',response_model=RoleOut)
def role_active(id:int,body:Active):
    mutate('CALL set_role_active(:id,:is_active)',{'id':id,**body.model_dump()});return record('SELECT * FROM role','role_id',id)
@app.get(PREFIX+'/roles/{id}/permissions',response_model=Page[PermissionOut])
def role_permissions(id:int,limit:Limit=50,offset:Offset=0):
    record('SELECT * FROM role','role_id',id)
    return page(PERMISSIONS+' JOIN role_permission rp USING(permission_id) WHERE rp.role_id=:id ORDER BY p.permission_id',{'id':id},limit,offset)
@app.post(PREFIX+'/roles/{id}/permissions/{permission_id}',status_code=201)
def grant(id:int,permission_id:int):
    mutate('CALL grant_role_permission(:id,:permission)',{'id':id,'permission':permission_id});return {'role_id':id,'permission_id':permission_id}
@app.delete(PREFIX+'/roles/{id}/permissions/{permission_id}',status_code=204)
def remove_grant(id:int,permission_id:int):
    mutate('CALL revoke_role_permission(:id,:permission)',{'id':id,'permission':permission_id});return Response(status_code=204)

@app.get(PREFIX+'/resources',response_model=Page[ResourceOut])
def resources(limit:Limit=50,offset:Offset=0):return page('SELECT * FROM resource ORDER BY resource_id',{},limit,offset)
@app.post(PREFIX+'/resources',response_model=ResourceOut,status_code=201)
def create_resource(body:ResourceIn):
    r=mutate('SELECT create_resource(:resource_code,:name,:type) resource_id',body.model_dump());return record('SELECT * FROM resource','resource_id',r['resource_id'])
@app.patch(PREFIX+'/resources/{id}',response_model=ResourceOut)
def resource_active(id:int,body:Active):
    mutate('CALL set_resource_active(:id,:is_active)',{'id':id,**body.model_dump()});return record('SELECT * FROM resource','resource_id',id)
@app.get(PREFIX+'/permissions',response_model=Page[PermissionOut])
def permissions(limit:Limit=50,offset:Offset=0,resource_id:int|None=None):
    return page(PERMISSIONS+(' WHERE p.resource_id=:id' if resource_id is not None else '')+' ORDER BY p.permission_id',{'id':resource_id},limit,offset)
@app.post(PREFIX+'/permissions',response_model=PermissionOut,status_code=201)
def create_permission(body:PermissionIn):
    r=mutate('SELECT create_permission(:resource_id,:action_code) permission_id',body.model_dump());return record(PERMISSIONS,'p.permission_id',r['permission_id'])

@app.post(PREFIX+'/evaluations',response_model=EvaluationOut,responses={404:{'model':EvaluationOut}})
def evaluation(body:EvaluationIn):
    result=mutate('SELECT * FROM evaluate_access(:user_id,:permission_id)',body.model_dump())
    if result['log_id'] is None:return JSONResponse(status_code=404,content=jsonable_encoder(result))
    return result


def audit_filter(user_id,resource_id,decision,date_from,date_to,search):
    clauses=[];params={}
    for key,value in [('user_id',user_id),('resource_id',resource_id),('decision',decision)]:
        if value is not None: clauses.append(key+'=:'+key);params[key]=value
    if date_from is not None:clauses.append('occurred_at>=:date_from');params['date_from']=date_from
    if date_to is not None:clauses.append('occurred_at<:date_to');params['date_to']=date_to
    if date_from and date_to and date_from>=date_to:raise HTTPException(422,'Start must be before end; end is exclusive.')
    if search:
        clauses.append('(full_name ILIKE :search OR email ILIKE :search OR resource_code ILIKE :search OR action_code ILIKE :search)');params['search']='%'+search+'%'
    return (' WHERE '+' AND '.join(clauses) if clauses else ''),params

@app.get(PREFIX+'/audit',response_model=Page[AuditOut])
def audit(limit:Limit=25,offset:Offset=0,user_id:int|None=None,resource_id:int|None=None,
          decision:Literal['ALLOW','DENY']|None=None,date_from:AwareDatetime|None=None,date_to:AwareDatetime|None=None,
          search:str=Query('',max_length=150)):
    where,params=audit_filter(user_id,resource_id,decision,date_from,date_to,search)
    return page('SELECT * FROM vw_access_audit_history'+where+' ORDER BY occurred_at DESC,log_id DESC',params,limit,offset)
@app.get(PREFIX+'/reports/audit-summary')
def audit_summary(user_id:int|None=None,resource_id:int|None=None,decision:Literal['ALLOW','DENY']|None=None,
                  date_from:AwareDatetime|None=None,date_to:AwareDatetime|None=None,search:str=Query('',max_length=150)):
    where,params=audit_filter(user_id,resource_id,decision,date_from,date_to,search)
    return one("SELECT count(*) total_events,count(*) FILTER(WHERE decision='ALLOW') allow_count,count(*) FILTER(WHERE decision='DENY') deny_count FROM vw_access_audit_history"+where,params)
@app.get(PREFIX+'/reports/dashboard',response_model=Dashboard)
def dashboard():
    return one("""SELECT (SELECT count(*) FROM app_user) total_users,(SELECT count(*) FROM role WHERE is_active) active_roles,
    (SELECT count(*) FROM resource) total_resources,count(*) total_events,count(*) FILTER(WHERE decision='ALLOW') allow_count,
    count(*) FILTER(WHERE decision='DENY') deny_count FROM access_log""")
@app.get(PREFIX+'/reports/activity')
def activity(limit:Limit=50,offset:Offset=0):return page('SELECT * FROM generate_access_activity_summary() ORDER BY user_id',{},limit,offset)
@app.get(PREFIX+'/reports/resources')
def resource_report(limit:Limit=50,offset:Offset=0):return page('SELECT * FROM vw_resource_access_summary ORDER BY attempts DESC,resource_id',{},limit,offset)
@app.get(PREFIX+'/reports/denials')
def denial_report(limit:Limit=50,offset:Offset=0):return page('SELECT * FROM vw_denied_access_summary ORDER BY denied_attempts DESC,user_id',{},limit,offset)
@app.get(PREFIX+'/reports/users-without-permissions',response_model=Page[UserOut])
def no_permissions(limit:Limit=50,offset:Offset=0):return page(USERS+' WHERE NOT EXISTS(SELECT 1 FROM vw_effective_user_permissions e WHERE e.user_id=u.user_id) ORDER BY u.user_id',{},limit,offset)
@app.get(PREFIX+'/reports/sensitive-permissions')
def sensitive(limit:Limit=50,offset:Offset=0):
    return page("SELECT r.role_id,r.role_name,s.resource_code,p.action_code FROM role r JOIN role_permission rp USING(role_id) JOIN permission p USING(permission_id) JOIN resource s USING(resource_id) WHERE p.action_code IN ('WRITE','EXECUTE','ADMIN') ORDER BY r.role_id,p.permission_id",{},limit,offset)
