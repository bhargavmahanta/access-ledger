"""
AccessLedger — database integrity tests (Review 1 section 14, database group).

Every test asserts a constraint at the DATABASE level. None of them re-implements
the rule in Python: each one performs a legal-looking operation and expects the
database to refuse it, so a passing run is evidence the constraint lives in the
schema rather than in application code.

Run:  .venv/bin/pytest tests/database -v
"""

import os

import psycopg
import pytest
from psycopg import errors
from psycopg.rows import dict_row

PGHOST = os.environ.get("PGHOST", str(
    __import__("pathlib").Path(__file__).resolve().parents[2] / ".pgsock"))
PGPORT = os.environ.get("PGPORT", "55432")
PGUSER = os.environ.get("PGUSER", "postgres")
PGDATABASE = os.environ.get("PGDATABASE", "accessledger")


def connect():
    return psycopg.connect(
        host=PGHOST, port=PGPORT, user=PGUSER, dbname=PGDATABASE,
        autocommit=True, row_factory=dict_row,
    )


@pytest.fixture
def db():
    """Every test runs in its own transaction that is always rolled back, so the
    seed data is untouched no matter how a test ends."""
    with connect() as conn:
        with conn.transaction():
            yield conn
            raise psycopg.Rollback


@pytest.fixture
def ids(db):
    """Natural keys from the seed, resolved to surrogate keys per test."""
    return {
        "dept_cs": db.execute(
            "SELECT department_id FROM department WHERE department_name='Computer Science'"
        ).fetchone()["department_id"],
        "user_priya": db.execute(
            "SELECT user_id FROM app_user WHERE email='priya.sharma@uni.edu'"
        ).fetchone()["user_id"],
        "user_chen": db.execute(
            "SELECT user_id FROM app_user WHERE email='chen.wei@uni.edu'"
        ).fetchone()["user_id"],
        "user_aisha": db.execute(
            "SELECT user_id FROM app_user WHERE email='aisha.bello@uni.edu'"
        ).fetchone()["user_id"],
        "role_viewer": db.execute(
            "SELECT role_id FROM role WHERE role_name='Viewer'"
        ).fetchone()["role_id"],
        "res_db": db.execute(
            "SELECT resource_id FROM resource WHERE resource_code='RES-DB-01'"
        ).fetchone()["resource_id"],
    }


# ---------------------------------------------------------------------------
# FR-01  Departments and users
# ---------------------------------------------------------------------------
class test_valid_inserts:
    def test_valid_user_is_accepted(self, db, ids):
        row = db.execute(
            "INSERT INTO app_user (department_id, full_name, email) "
            "VALUES (%s, %s, %s) RETURNING user_id, status",
            (ids["dept_cs"], "Test Person", "test.person@uni.edu"),
        ).fetchone()
        assert row["user_id"] is not None
        assert row["status"] == "ACTIVE", "default status must be ACTIVE"

    def test_email_is_stored_normalized(self, db, ids):
        row = db.execute(
            "INSERT INTO app_user (department_id, full_name, email) "
            "VALUES (%s, %s, %s) RETURNING email",
            (ids["dept_cs"], "Mixed Case", "  Mixed.Case@Uni.EDU  "),
        ).fetchone()
        assert row["email"] == "mixed.case@uni.edu", \
            "the BEFORE trigger must strip and lowercase before storage"

    def test_invalid_department_reference_is_rejected(self, db, ids):
        with pytest.raises(errors.ForeignKeyViolation):
            db.execute(
                "INSERT INTO app_user (department_id, full_name, email) "
                "VALUES (%s, %s, %s)", (999999, "Ghost", "ghost@uni.edu"))


class test_unique_constraints:
    def test_duplicate_department_name(self, db):
        with pytest.raises(errors.UniqueViolation):
            db.execute("INSERT INTO department (department_name) VALUES ('Finance')")

    def test_duplicate_email(self, db, ids):
        with pytest.raises(errors.UniqueViolation):
            db.execute(
                "INSERT INTO app_user (department_id, full_name, email) "
                "VALUES (%s, %s, %s)", (ids["dept_cs"], "Clone", "priya.sharma@uni.edu"))

    def test_duplicate_email_differing_only_by_case_and_whitespace(self, db, ids):
        """Normalization must happen BEFORE the uniqueness check, or 'P.S@Uni.edu '
        and ' p.s@uni.edu ' would both be accepted."""
        with pytest.raises(errors.UniqueViolation):
            db.execute(
                "INSERT INTO app_user (department_id, full_name, email) "
                "VALUES (%s, %s, %s)",
                (ids["dept_cs"], "Sneaky", "  Priya.Sharma@UNI.edu "))

    def test_duplicate_role_name(self, db):
        with pytest.raises(errors.UniqueViolation):
            db.execute("INSERT INTO role (role_name) VALUES ('Viewer')")

    def test_duplicate_resource_code(self, db):
        with pytest.raises(errors.UniqueViolation):
            db.execute(
                "INSERT INTO resource (resource_code, name, type) "
                "VALUES ('RES-DB-01', 'Copy', 'DATABASE')")

    def test_duplicate_permission_for_same_resource(self, db, ids):
        """UNIQUE(resource_id, action_code): RES-DB-01 already defines READ."""
        with pytest.raises(errors.UniqueViolation):
            db.execute(
                "INSERT INTO permission (resource_id, action_code) VALUES (%s, 'READ')",
                (ids["res_db"],))

    def test_same_action_on_a_different_resource_is_allowed(self, db, ids):
        """The constraint is on the PAIR, not on action_code alone.
        RES-DOC-04 defines only READ, so WRITE on it is a new pair."""
        res_doc = db.execute(
            "SELECT resource_id FROM resource WHERE resource_code='RES-DOC-04'"
        ).fetchone()["resource_id"]
        row = db.execute(
            "INSERT INTO permission (resource_id, action_code) "
            "VALUES (%s, 'WRITE') RETURNING permission_id", (res_doc,)).fetchone()
        assert row["permission_id"] is not None


class test_composite_primary_keys:
    def test_duplicate_user_role_pair_is_rejected(self, db, ids):
        with pytest.raises(errors.UniqueViolation):
            db.execute("INSERT INTO user_role (user_id, role_id) VALUES (%s, %s)",
                       (ids["user_priya"], ids["role_viewer"]))

    def test_duplicate_role_permission_pair_is_rejected(self, db):
        pair = db.execute(
            "SELECT role_id, permission_id FROM role_permission LIMIT 1").fetchone()
        with pytest.raises(errors.UniqueViolation):
            db.execute("INSERT INTO role_permission (role_id, permission_id) "
                       "VALUES (%s, %s)", (pair["role_id"], pair["permission_id"]))

    def test_same_role_granted_to_a_different_user_is_allowed(self, db, ids):
        row = db.execute(
            "INSERT INTO user_role (user_id, role_id) VALUES (%s, %s) RETURNING user_id",
            (ids["user_chen"], ids["role_viewer"])).fetchone()
        assert row["user_id"] == ids["user_chen"]

    def test_assigned_at_defaults_to_a_timestamp(self, db, ids):
        row = db.execute(
            "INSERT INTO user_role (user_id, role_id) VALUES (%s, %s) RETURNING assigned_at",
            (ids["user_chen"], ids["role_viewer"])).fetchone()
        assert row["assigned_at"] is not None


class test_check_constraints:
    def test_invalid_user_status(self, db, ids):
        with pytest.raises(errors.CheckViolation):
            db.execute(
                "INSERT INTO app_user (department_id, full_name, email, status) "
                "VALUES (%s, %s, %s, 'RETIRED')",
                (ids["dept_cs"], "Odd", "odd@uni.edu"))

    def test_invalid_decision_value(self, db, ids):
        """decision is generated, so the only way to supply a bad one is a bad
        reason_code -- which the CHECK must refuse."""
        perm = db.execute("SELECT permission_id FROM permission LIMIT 1").fetchone()
        with pytest.raises(errors.CheckViolation):
            db.execute(
                "INSERT INTO access_log (user_id, permission_id, reason_code) "
                "VALUES (%s, %s, 'MAYBE')", (ids["user_priya"], perm["permission_id"]))

    def test_every_reason_code_in_the_vocabulary_is_accepted(self, db, ids):
        perm = db.execute("SELECT permission_id FROM permission LIMIT 1").fetchone()
        for code in ("PERMISSION_GRANTED", "USER_DISABLED", "RESOURCE_INACTIVE",
                     "NO_ACTIVE_ROLE", "PERMISSION_NOT_GRANTED"):
            db.execute(
                "INSERT INTO access_log (user_id, permission_id, reason_code) "
                "VALUES (%s, %s, %s)", (ids["user_priya"], perm["permission_id"], code))

    def test_decision_is_derived_not_supplied(self, db, ids):
        """The brief requires the caller not to choose the decision. Insert the
        pair twice with the two reason codes and check what the database kept."""
        perm = db.execute("SELECT permission_id FROM permission LIMIT 1").fetchone()
        allow = db.execute(
            "INSERT INTO access_log (user_id, permission_id, reason_code) "
            "VALUES (%s, %s, 'PERMISSION_GRANTED') RETURNING decision",
            (ids["user_priya"], perm["permission_id"])).fetchone()
        deny = db.execute(
            "INSERT INTO access_log (user_id, permission_id, reason_code) "
            "VALUES (%s, %s, 'NO_ACTIVE_ROLE') RETURNING decision",
            (ids["user_priya"], perm["permission_id"])).fetchone()
        assert allow["decision"] == "ALLOW"
        assert deny["decision"] == "DENY"

    def test_decision_cannot_be_overridden_explicitly(self, db, ids):
        perm = db.execute("SELECT permission_id FROM permission LIMIT 1").fetchone()
        with pytest.raises(errors.Error):
            db.execute(
                "INSERT INTO access_log (user_id, permission_id, reason_code, decision) "
                "VALUES (%s, %s, 'PERMISSION_NOT_GRANTED', 'ALLOW')",
                (ids["user_priya"], perm["permission_id"]))


class test_referential_integrity:
    def test_access_log_rejects_unknown_user(self, db):
        perm = db.execute("SELECT permission_id FROM permission LIMIT 1").fetchone()
        with pytest.raises(errors.ForeignKeyViolation):
            db.execute(
                "INSERT INTO access_log (user_id, permission_id, reason_code) "
                "VALUES (999999, %s, 'NO_ACTIVE_ROLE')", (perm["permission_id"],))

    def test_access_log_rejects_unknown_permission(self, db, ids):
        with pytest.raises(errors.ForeignKeyViolation):
            db.execute(
                "INSERT INTO access_log (user_id, permission_id, reason_code) "
                "VALUES (%s, 999999, 'PERMISSION_NOT_GRANTED')", (ids["user_priya"],))

    def test_user_role_rejects_unknown_role(self, db, ids):
        with pytest.raises(errors.ForeignKeyViolation):
            db.execute("INSERT INTO user_role (user_id, role_id) VALUES (%s, 999999)",
                       (ids["user_priya"],))

    def test_department_holding_users_cannot_be_deleted(self, db, ids):
        with pytest.raises(errors.ForeignKeyViolation):
            db.execute("DELETE FROM department WHERE department_id = %s", (ids["dept_cs"],))


# ---------------------------------------------------------------------------
# FR-05 / FR-07  Audit retention
# ---------------------------------------------------------------------------
class test_audit_protection:
    def test_access_log_update_is_refused(self, db):
        log = db.execute("SELECT log_id FROM access_log LIMIT 1").fetchone()
        with pytest.raises(errors.RestrictViolation):
            db.execute("UPDATE access_log SET reason_code='NO_ACTIVE_ROLE' "
                       "WHERE log_id=%s", (log["log_id"],))

    def test_access_log_delete_is_refused(self, db):
        log = db.execute("SELECT log_id FROM access_log LIMIT 1").fetchone()
        with pytest.raises(errors.RestrictViolation):
            db.execute("DELETE FROM access_log WHERE log_id=%s", (log["log_id"],))

    def test_access_log_truncate_is_refused(self, db):
        with pytest.raises(errors.RestrictViolation):
            db.execute("TRUNCATE access_log")

    def test_permission_referenced_by_a_log_cannot_be_redefined(self, db):
        """'New meanings require new permission records' -- rewriting the resource
        or action of a logged permission would silently change history."""
        perm = db.execute(
            "SELECT permission_id, resource_id FROM permission p "
            "WHERE EXISTS (SELECT 1 FROM access_log l "
            "              WHERE l.permission_id = p.permission_id) LIMIT 1").fetchone()
        with pytest.raises(errors.RestrictViolation):
            db.execute("UPDATE permission SET action_code='REDEFINE_ME' "
                       "WHERE permission_id=%s", (perm["permission_id"],))

    def test_unreferenced_permission_can_still_be_corrected(self, db):
        """The freeze applies only once history exists -- a typo in a definition
        nobody has used must remain fixable."""
        perm = db.execute(
            "INSERT INTO permission (resource_id, action_code) "
            "SELECT resource_id, 'TYPO_TYPO' FROM resource LIMIT 1 "
            "RETURNING permission_id").fetchone()
        db.execute("UPDATE permission SET action_code='EXECUTE' WHERE permission_id=%s",
                   (perm["permission_id"],))

    def test_permission_referenced_by_a_log_cannot_be_deleted(self, db):
        perm = db.execute(
            "SELECT permission_id FROM permission p "
            "WHERE EXISTS (SELECT 1 FROM access_log l "
            "              WHERE l.permission_id = p.permission_id) LIMIT 1").fetchone()
        with pytest.raises(errors.ForeignKeyViolation):
            db.execute("DELETE FROM permission WHERE permission_id=%s",
                       (perm["permission_id"],))

    def test_deactivated_user_and_their_history_survive(self, db, ids):
        """FR-07: deactivation, never deletion."""
        db.execute("UPDATE app_user SET status='DISABLED' WHERE user_id=%s",
                   (ids["user_aisha"],))
        row = db.execute(
            "SELECT u.status, COUNT(l.log_id) AS events FROM app_user u "
            "LEFT JOIN access_log l ON l.user_id = u.user_id "
            "WHERE u.user_id=%s GROUP BY u.status", (ids["user_aisha"],)).fetchone()
        assert row["status"] == "DISABLED"
        assert row["events"] > 0, "audit history must remain after deactivation"

    def test_repeated_attempts_each_keep_their_own_log_id(self, db, ids):
        """FR-05: identical attempts are still distinguishable."""
        perm = db.execute("SELECT permission_id FROM permission LIMIT 1").fetchone()
        new = db.execute(
            "INSERT INTO access_log (user_id, permission_id, reason_code) "
            "VALUES (%s, %s, 'PERMISSION_NOT_GRANTED') RETURNING log_id",
            (ids["user_priya"], perm["permission_id"])).fetchone()["log_id"]
        db.execute("INSERT INTO access_log (user_id, permission_id, reason_code) "
                   "VALUES (%s, %s, 'PERMISSION_NOT_GRANTED')",
                   (ids["user_priya"], perm["permission_id"]))
        count = db.execute(
            "SELECT COUNT(*) AS n FROM access_log WHERE user_id=%s AND permission_id=%s",
            (ids["user_priya"], perm["permission_id"])).fetchone()["n"]
        assert count >= 2
        assert new not in (None,)


# ---------------------------------------------------------------------------
# FR-04  Effective permissions (the derived answer the views must give)
# ---------------------------------------------------------------------------
class test_effective_permissions:
    def test_active_user_with_permission_is_listed(self, db):
        row = db.execute(
            "SELECT COUNT(*) AS n FROM vw_effective_user_permissions "
            "WHERE email='priya.sharma@uni.edu' AND resource_code='RES-DB-01' "
            "AND action_code='READ'").fetchone()
        assert row["n"] == 1

    def test_two_role_paths_yield_one_effective_permission(self, db):
        """UNION semantics: Viewer and Analyst both grant Priya RES-DB-01:READ."""
        paths = db.execute(
            "SELECT COUNT(*) AS n FROM user_role ur "
            "JOIN role r ON r.role_id = ur.role_id "
            "JOIN role_permission rp ON rp.role_id = r.role_id "
            "JOIN permission p ON p.permission_id = rp.permission_id "
            "JOIN resource s ON s.resource_id = p.resource_id "
            "JOIN app_user u ON u.user_id = ur.user_id "
            "WHERE u.email='priya.sharma@uni.edu' AND s.resource_code='RES-DB-01' "
            "AND p.action_code='READ' AND u.status='ACTIVE' AND r.is_active "
            "AND s.is_active").fetchone()["n"]
        effective = db.execute(
            "SELECT COUNT(*) AS n FROM vw_effective_user_permissions "
            "WHERE email='priya.sharma@uni.edu' AND resource_code='RES-DB-01' "
            "AND action_code='READ'").fetchone()["n"]
        assert paths == 2 and effective == 1

    def test_disabled_user_has_no_effective_permissions(self, db):
        row = db.execute(
            "SELECT COUNT(*) AS n FROM vw_effective_user_permissions "
            "WHERE email='aisha.bello@uni.edu'").fetchone()
        assert row["n"] == 0

    def test_user_without_roles_has_no_effective_permissions(self, db):
        row = db.execute(
            "SELECT COUNT(*) AS n FROM vw_effective_user_permissions "
            "WHERE email='chen.wei@uni.edu'").fetchone()
        assert row["n"] == 0

    def test_disabled_resource_contributes_no_effective_permission(self, db):
        row = db.execute(
            "SELECT COUNT(*) AS n FROM vw_effective_user_permissions "
            "WHERE resource_code='RES-DOC-04'").fetchone()
        assert row["n"] == 0, "RES-DOC-04 is inactive, so nobody holds it effectively"

    def test_disabled_role_contributes_no_effective_permission(self, db, ids):
        """Proved in isolation: the seeded Legacy Contractor shares both its
        permissions with active roles, so the seed cannot demonstrate this.
        Build a role that is the ONLY supplier of a brand-new permission, leave
        it inactive, and assert the permission never becomes effective."""
        perm = db.execute(
            "INSERT INTO permission (resource_id, action_code) "
            "SELECT resource_id, 'ADMIN' FROM resource WHERE resource_code='RES-SRV-03' "
            "RETURNING permission_id").fetchone()["permission_id"]
        role = db.execute(
            "INSERT INTO role (role_name, is_active) VALUES ('Disabled Test Role', FALSE) "
            "RETURNING role_id").fetchone()["role_id"]
        db.execute("INSERT INTO role_permission (role_id, permission_id) VALUES (%s, %s)",
                   (role, perm))
        db.execute("INSERT INTO user_role (user_id, role_id) VALUES (%s, %s)",
                   (ids["user_priya"], role))

        n = db.execute(
            "SELECT COUNT(*) AS n FROM vw_effective_user_permissions "
            "WHERE permission_id = %s", (perm,)).fetchone()["n"]
        assert n == 0, "an inactive role must supply no effective permission"

        # Reactivating the same role, with no other change, must make it appear.
        db.execute("UPDATE role SET is_active = TRUE WHERE role_id = %s", (role,))
        n_after = db.execute(
            "SELECT COUNT(*) AS n FROM vw_effective_user_permissions "
            "WHERE permission_id = %s", (perm,)).fetchone()["n"]
        assert n_after == 1, "reactivating the role must restore the permission"


# ---------------------------------------------------------------------------
# FR-07  Revocation
# ---------------------------------------------------------------------------
class test_revocation:
    def test_revoking_a_role_removes_effective_access(self, db, ids):
        before = db.execute(
            "SELECT COUNT(*) AS n FROM vw_effective_user_permissions "
            "WHERE email='priya.sharma@uni.edu'").fetchone()["n"]
        db.execute("DELETE FROM user_role WHERE user_id=%s AND role_id=%s",
                   (ids["user_priya"], ids["role_viewer"]))
        after = db.execute(
            "SELECT COUNT(*) AS n FROM vw_effective_user_permissions "
            "WHERE email='priya.sharma@uni.edu'").fetchone()["n"]
        assert after < before, "revocation must reduce current access"

    def test_revocation_leaves_past_events_intact(self, db, ids):
        """The core of FR-07: revoking access changes the future, not the past."""
        past = db.execute(
            "SELECT COUNT(*) AS n FROM access_log WHERE user_id=%s",
            (ids["user_priya"],)).fetchone()["n"]
        db.execute("DELETE FROM user_role WHERE user_id=%s", (ids["user_priya"],))
        remaining = db.execute(
            "SELECT COUNT(*) AS n FROM access_log WHERE user_id=%s",
            (ids["user_priya"],)).fetchone()["n"]
        assert remaining == past