from datetime import datetime
from typing import Generic, TypeVar, Literal, Annotated
from pydantic import BaseModel, ConfigDict, Field, EmailStr, AwareDatetime, StringConstraints

Name=Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=150)]
Action=Annotated[str,StringConstraints(strip_whitespace=True,to_upper=True,min_length=1,max_length=40,pattern=r'^[A-Za-z][A-Za-z0-9_]*$')]
Positive=Annotated[int,Field(gt=0)]
class Input(BaseModel):
    model_config=ConfigDict(extra='forbid')
class DepartmentIn(Input): department_name: Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=100)]
class DepartmentOut(DepartmentIn): department_id:int
class UserIn(Input):
    department_id:Positive
    full_name:Name
    email:EmailStr=Field(max_length=254)
class UserOut(UserIn):
    user_id:int
    status:Literal['ACTIVE','DISABLED']
    department_name:str
class UserStatus(Input): status:Literal['ACTIVE','DISABLED']
class RoleIn(Input): role_name:Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=80)]
class RoleOut(RoleIn):
    role_id:int
    is_active:bool
class Active(Input): is_active:bool
class ResourceIn(Input):
    resource_code:Annotated[str,StringConstraints(strip_whitespace=True,min_length=1,max_length=50)]
    name:Name
    type:Annotated[str,StringConstraints(strip_whitespace=True,to_upper=True,min_length=1,max_length=30)]
class ResourceOut(ResourceIn):
    resource_id:int
    is_active:bool
class PermissionIn(Input):
    resource_id:Positive
    action_code:Action
class PermissionOut(PermissionIn):
    permission_id:int
    resource_code:str
    resource_name:str
class EvaluationIn(Input):
    user_id:Positive
    permission_id:Positive
class EvaluationOut(BaseModel):
    decision:Literal['ALLOW','DENY']
    reason_code:str
    log_id:int|None
    occurred_at:datetime|None
class AuditOut(BaseModel):
    log_id:int
    occurred_at:datetime
    decision:Literal['ALLOW','DENY']
    reason_code:str
    user_id:int
    email:str
    full_name:str
    department_name:str
    permission_id:int
    resource_id:int
    resource_code:str
    resource_name:str
    resource_type:str
    action_code:str
T=TypeVar('T')
class Page(BaseModel,Generic[T]):
    items:list[T]
    total:int
    limit:int
    offset:int
class Dashboard(BaseModel):
    total_users:int
    active_roles:int
    total_resources:int
    total_events:int
    allow_count:int
    deny_count:int
