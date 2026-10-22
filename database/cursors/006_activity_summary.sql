-- Explicit OPEN/FETCH/CLOSE cursor: emits one report row per user, including zero activity.
CREATE FUNCTION generate_access_activity_summary()
RETURNS TABLE(user_id integer,full_name varchar,total_attempts bigint,allowed_attempts bigint,denied_attempts bigint)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE c_users CURSOR FOR SELECT u.user_id,u.full_name FROM public.app_user u ORDER BY u.user_id;
        v_user record;
BEGIN
 OPEN c_users;
 LOOP
  FETCH c_users INTO v_user; EXIT WHEN NOT FOUND;
  user_id:=v_user.user_id; full_name:=v_user.full_name;
  SELECT count(*),count(*) FILTER(WHERE l.decision='ALLOW'),count(*) FILTER(WHERE l.decision='DENY')
  INTO total_attempts,allowed_attempts,denied_attempts FROM public.access_log l WHERE l.user_id=v_user.user_id;
  RETURN NEXT;
 END LOOP;
 CLOSE c_users;
END $$;
