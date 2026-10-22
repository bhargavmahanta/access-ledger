-- Baseline DDL. Apply once through Alembic or scripts/apply-sql.sh.
-- 1. DEPARTMENT -----------------------------------------------------------------
CREATE TABLE department (
    department_id   INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    CONSTRAINT uq_department_name UNIQUE (department_name)
);


-- 2. APP_USER -------------------------------------------------------------------
-- One row per registered person. status is the only lifecycle control: a user is
-- never deleted while assignments or audit events reference them.
CREATE TABLE app_user (
    user_id       INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_id INTEGER      NOT NULL,
    full_name     VARCHAR(150) NOT NULL,
    email         VARCHAR(254) NOT NULL,
    status        VARCHAR(10)  NOT NULL DEFAULT 'ACTIVE',
    CONSTRAINT fk_app_user_department FOREIGN KEY (department_id)
        REFERENCES department (department_id) ON DELETE RESTRICT,
    CONSTRAINT ck_app_user_status CHECK (status IN ('ACTIVE', 'DISABLED')),
    -- Uniqueness applies to the normalized value; see trg_app_user_email_normalize.
    CONSTRAINT uq_app_user_email UNIQUE (email)
);

CREATE INDEX ix_app_user_department ON app_user (department_id);


-- 3. ROLE -----------------------------------------------------------------------
CREATE TABLE role (
    role_id   INTEGER     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name VARCHAR(80) NOT NULL,
    is_active BOOLEAN     NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_role_name UNIQUE (role_name)
);


-- 4. USER_ROLE ------------------------------------------------------------------
-- Resolves the user <-> role many-to-many relationship. The composite primary key
-- IS the duplicate-assignment guard: a second identical row is a key violation.
CREATE TABLE user_role (
    user_id     INTEGER     NOT NULL,
    role_id     INTEGER     NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_user_role PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_role_user FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_user_role_role FOREIGN KEY (role_id)
        REFERENCES role (role_id) ON DELETE RESTRICT
);

CREATE INDEX ix_user_role_role ON user_role (role_id);


-- 5. RESOURCE -------------------------------------------------------------------
-- type is an open vocabulary (DATABASE, APPLICATION, SERVER, DOCUMENT are
-- examples, not a closed set) -- see database-design.md 4.4.
CREATE TABLE resource (
    resource_id   INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resource_code VARCHAR(50)  NOT NULL,
    name          VARCHAR(150) NOT NULL,
    type          VARCHAR(30)  NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_resource_code UNIQUE (resource_code)
);


-- 6. PERMISSION -----------------------------------------------------------------
-- One row = one action on one resource. UNIQUE(resource_id, action_code) is the
-- candidate key the normalization analysis relies on.
CREATE TABLE permission (
    permission_id INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    resource_id   INTEGER      NOT NULL,
    action_code   VARCHAR(40)  NOT NULL,
    CONSTRAINT fk_permission_resource FOREIGN KEY (resource_id)
        REFERENCES resource (resource_id) ON DELETE RESTRICT,
    CONSTRAINT uq_permission_resource_action UNIQUE (resource_id, action_code)
);


-- 7. ROLE_PERMISSION ------------------------------------------------------------
CREATE TABLE role_permission (
    role_id       INTEGER     NOT NULL,
    permission_id INTEGER     NOT NULL,
    granted_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_role_permission PRIMARY KEY (role_id, permission_id),
    CONSTRAINT fk_role_permission_role FOREIGN KEY (role_id)
        REFERENCES role (role_id) ON DELETE RESTRICT,
    CONSTRAINT fk_role_permission_permission FOREIGN KEY (permission_id)
        REFERENCES permission (permission_id) ON DELETE RESTRICT
);

CREATE INDEX ix_role_permission_permission ON role_permission (permission_id);


-- 8. ACCESS_LOG -----------------------------------------------------------------
-- reason_code is the controlled vocabulary (database-design.md 4.3). decision is
-- GENERATED rather than stored independently: ALLOW is exactly what
-- PERMISSION_GRANTED means, so letting a caller set the two separately would
-- permit impossible pairs such as ALLOW + USER_DISABLED. This also satisfies the
-- brief's "the caller must not arbitrarily choose the logged decision".
CREATE TABLE access_log (
    log_id        INTEGER     GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id       INTEGER     NOT NULL,
    permission_id INTEGER     NOT NULL,
    occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    decision      VARCHAR(5)  GENERATED ALWAYS AS
                  (CASE WHEN reason_code = 'PERMISSION_GRANTED' THEN 'ALLOW' ELSE 'DENY' END)
                  STORED NOT NULL,
    reason_code   VARCHAR(25) NOT NULL,
    CONSTRAINT fk_access_log_user FOREIGN KEY (user_id)
        REFERENCES app_user (user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_access_log_permission FOREIGN KEY (permission_id)
        REFERENCES permission (permission_id) ON DELETE RESTRICT,
    CONSTRAINT ck_access_log_reason CHECK (reason_code IN (
        'PERMISSION_GRANTED',    -- ALLOW
        'USER_DISABLED',         -- DENY: user is not active
        'RESOURCE_INACTIVE',     -- DENY: resource is not active
        'NO_ACTIVE_ROLE',        -- DENY: no assigned role is active
        'PERMISSION_NOT_GRANTED' -- DENY: no active role contains the permission
    ))
);

-- Supporting the two audit-report access paths (FR-06); performance analysis in
-- Review 3 will decide whether these are the right indexes.
CREATE INDEX ix_access_log_user_time       ON access_log (user_id, occurred_at DESC);
CREATE INDEX ix_access_log_permission_time ON access_log (permission_id, occurred_at DESC);


-- ----------------------------------------------------------------------------
-- Integrity triggers
-- ----------------------------------------------------------------------------

-- Email normalization (database-design.md 4.2). Runs BEFORE the unique check so
-- that " Ann.Smith@Uni.EDU " and "ann.smith@uni.edu" collide as they must.
CREATE FUNCTION normalize_app_user_email() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.email := lower(btrim(NEW.email));
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_app_user_email_normalize
    BEFORE INSERT OR UPDATE OF email ON app_user
    FOR EACH ROW EXECUTE FUNCTION normalize_app_user_email();


-- ACCESS_LOG is append-only (FR-05). A trigger rather than privileges alone,
-- because privileges do not constrain the table owner.
CREATE FUNCTION access_log_is_append_only() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'ACCESS_LOG is append-only; % is not permitted', TG_OP
        USING ERRCODE = 'restrict_violation';
END;
$$;

CREATE TRIGGER trg_access_log_append_only
    BEFORE UPDATE OR DELETE ON access_log
    FOR EACH ROW EXECUTE FUNCTION access_log_is_append_only();

CREATE TRIGGER trg_access_log_append_only_trunc
    BEFORE TRUNCATE ON access_log
    FOR EACH STATEMENT EXECUTE FUNCTION access_log_is_append_only();


-- A permission's meaning is frozen once audit events reference it: changing
-- resource_id or action_code would silently rewrite history (database-design.md 4.6).
CREATE FUNCTION permission_meaning_is_frozen() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM access_log WHERE permission_id = OLD.permission_id)
       AND (NEW.resource_id, NEW.action_code)
           IS DISTINCT FROM (OLD.resource_id, OLD.action_code) THEN
        RAISE EXCEPTION
            'PERMISSION % is referenced by ACCESS_LOG; its resource and action cannot change. '
            'Create a new permission instead.', OLD.permission_id
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_permission_meaning_frozen
    BEFORE UPDATE OF resource_id, action_code ON permission
    FOR EACH ROW EXECUTE FUNCTION permission_meaning_is_frozen();


