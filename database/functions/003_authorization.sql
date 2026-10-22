-- Controlled routines run as accessledger_demo_owner. All policy paths lock first.
CREATE FUNCTION policy_lock(p_shared boolean DEFAULT false) RETURNS void
LANGUAGE plpgsql VOLATILE SET search_path = pg_catalog, public, pg_temp AS $$
BEGIN
 IF current_setting('transaction_isolation') <> 'read committed' THEN
  RAISE EXCEPTION 'Controlled operations require READ COMMITTED' USING ERRCODE='25000';
 END IF;
 IF p_shared THEN PERFORM pg_advisory_xact_lock_shared(302, 8);
 ELSE PERFORM pg_advisory_xact_lock(302, 8); END IF;
END $$;

CREATE FUNCTION evaluate_access(p_user_id integer, p_permission_id integer)
RETURNS TABLE(decision varchar, reason_code varchar, log_id integer, occurred_at timestamptz)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER
SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE v_status varchar; v_active boolean; v_reason varchar;
BEGIN
 -- Separate VOLATILE PL/pgSQL statements obtain fresh READ COMMITTED snapshots
 -- after this lock has been acquired, including when acquisition had to wait.
 PERFORM public.policy_lock(true);
 SELECT u.status INTO v_status FROM public.app_user u WHERE u.user_id=p_user_id;
 IF NOT FOUND THEN
  RETURN QUERY SELECT 'DENY'::varchar,'USER_NOT_FOUND'::varchar,NULL::integer,NULL::timestamptz; RETURN;
 END IF;
 SELECT r.is_active INTO v_active FROM public.permission p JOIN public.resource r USING(resource_id)
 WHERE p.permission_id=p_permission_id;
 IF NOT FOUND THEN
  RETURN QUERY SELECT 'DENY'::varchar,'PERMISSION_NOT_FOUND'::varchar,NULL::integer,NULL::timestamptz; RETURN;
 END IF;
 IF v_status <> 'ACTIVE' THEN v_reason := 'USER_DISABLED';
 ELSIF NOT v_active THEN v_reason := 'RESOURCE_INACTIVE';
 ELSIF NOT EXISTS (SELECT 1 FROM public.user_role ur JOIN public.role r USING(role_id)
                  WHERE ur.user_id=p_user_id AND r.is_active) THEN v_reason := 'NO_ACTIVE_ROLE';
 ELSIF NOT EXISTS (SELECT 1 FROM public.user_role ur JOIN public.role r USING(role_id)
                  JOIN public.role_permission rp USING(role_id)
                  WHERE ur.user_id=p_user_id AND r.is_active AND rp.permission_id=p_permission_id)
 THEN v_reason := 'PERMISSION_NOT_GRANTED';
 ELSE v_reason := 'PERMISSION_GRANTED'; END IF;
 RETURN QUERY INSERT INTO public.access_log AS l(user_id,permission_id,reason_code,occurred_at)
 VALUES(p_user_id,p_permission_id,v_reason,clock_timestamp())
 RETURNING l.decision,l.reason_code,l.log_id,l.occurred_at;
END $$;

CREATE FUNCTION get_effective_permissions(p_user_id integer)
RETURNS TABLE(permission_id integer,resource_id integer,resource_code varchar,resource_name varchar,action_code varchar)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, public, pg_temp AS $$
 SELECT e.permission_id,e.resource_id,e.resource_code,e.resource_name,e.action_code
 FROM public.vw_effective_user_permissions e WHERE e.user_id=p_user_id ORDER BY e.resource_code,e.action_code;
$$;
