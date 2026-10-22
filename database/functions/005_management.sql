-- Creation and metadata edits use the same controlled policy boundary.
CREATE FUNCTION create_department(p_name varchar) RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE v_id integer;
BEGIN
 PERFORM public.policy_lock();
 INSERT INTO public.department(department_name) VALUES(p_name) RETURNING department_id INTO v_id; RETURN v_id;
END $$;
CREATE PROCEDURE update_department(p_id integer,p_name varchar)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 PERFORM public.policy_lock(); UPDATE public.department SET department_name=p_name WHERE department_id=p_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Department not found' USING ERRCODE='P0002'; END IF;
END $$;
CREATE FUNCTION create_user(p_department_id integer,p_full_name varchar,p_email varchar) RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE v_id integer;
BEGIN
 PERFORM public.policy_lock();
 INSERT INTO public.app_user(department_id,full_name,email) VALUES(p_department_id,p_full_name,p_email) RETURNING user_id INTO v_id; RETURN v_id;
END $$;
CREATE PROCEDURE update_user(p_id integer,p_department_id integer,p_full_name varchar,p_email varchar)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 PERFORM public.policy_lock();
 UPDATE public.app_user SET department_id=p_department_id,full_name=p_full_name,email=p_email WHERE user_id=p_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'User not found' USING ERRCODE='P0002'; END IF;
END $$;
CREATE FUNCTION create_role(p_name varchar) RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE v_id integer;
BEGIN
 PERFORM public.policy_lock(); INSERT INTO public.role(role_name) VALUES(p_name) RETURNING role_id INTO v_id; RETURN v_id;
END $$;
CREATE FUNCTION create_resource(p_code varchar,p_name varchar,p_type varchar) RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE v_id integer;
BEGIN
 PERFORM public.policy_lock();
 INSERT INTO public.resource(resource_code,name,type) VALUES(p_code,p_name,p_type) RETURNING resource_id INTO v_id; RETURN v_id;
END $$;
CREATE FUNCTION create_permission(p_resource_id integer,p_action_code varchar) RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE v_id integer;
BEGIN
 PERFORM public.policy_lock();
 INSERT INTO public.permission(resource_id,action_code) VALUES(p_resource_id,p_action_code) RETURNING permission_id INTO v_id; RETURN v_id;
END $$;
