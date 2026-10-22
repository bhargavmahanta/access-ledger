-- Separate roles avoid changing the historical database's application role.
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='accessledger_demo_owner') THEN
  CREATE ROLE accessledger_demo_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='accessledger_demo_app') THEN
  CREATE ROLE accessledger_demo_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
 END IF;
END $$;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE,CREATE ON SCHEMA public TO accessledger_demo_owner;
GRANT USAGE ON SCHEMA public TO accessledger_demo_app;
SET LOCAL ROLE accessledger_demo_owner;
