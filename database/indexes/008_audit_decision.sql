-- Latest filtered audit pages. Leading decision, descending time and stable ID.
CREATE INDEX IF NOT EXISTS ix_access_log_decision_time ON access_log(decision,occurred_at DESC,log_id DESC);
