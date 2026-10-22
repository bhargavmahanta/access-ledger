REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC,accessledger_demo_app;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC,accessledger_demo_app;
REVOKE ALL ON ALL ROUTINES IN SCHEMA public FROM PUBLIC,accessledger_demo_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO accessledger_demo_app;
GRANT EXECUTE ON FUNCTION evaluate_access(integer,integer),get_effective_permissions(integer),
 generate_access_activity_summary(),create_department(varchar),create_user(integer,varchar,varchar),
 create_role(varchar),create_resource(varchar,varchar,varchar),create_permission(integer,varchar)
 TO accessledger_demo_app;
GRANT EXECUTE ON PROCEDURE assign_user_role(integer,integer),revoke_user_role(integer,integer),
 grant_role_permission(integer,integer),revoke_role_permission(integer,integer),
 set_user_status(integer,varchar),set_role_active(integer,boolean),set_resource_active(integer,boolean),
 update_permission_identity(integer,integer,varchar),update_department(integer,varchar),
 update_user(integer,integer,varchar,varchar) TO accessledger_demo_app;
ALTER DEFAULT PRIVILEGES FOR ROLE accessledger_demo_owner IN SCHEMA public REVOKE EXECUTE ON ROUTINES FROM PUBLIC;
RESET ROLE;
