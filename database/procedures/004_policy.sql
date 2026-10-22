CREATE PROCEDURE assign_user_role(p_user_id integer,p_role_id integer)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE v_status varchar; v_active boolean;
BEGIN
 PERFORM public.policy_lock();
 SELECT status INTO v_status FROM public.app_user WHERE user_id=p_user_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'User not found' USING ERRCODE='P0002'; END IF;
 SELECT is_active INTO v_active FROM public.role WHERE role_id=p_role_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Role not found' USING ERRCODE='P0002'; END IF;
 IF v_status <> 'ACTIVE' OR NOT v_active THEN
  RAISE EXCEPTION 'Assignment requires an active user and role' USING ERRCODE='23514'; END IF;
 INSERT INTO public.user_role(user_id,role_id) VALUES(p_user_id,p_role_id);
END $$;

CREATE PROCEDURE revoke_user_role(p_user_id integer,p_role_id integer)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 PERFORM public.policy_lock();
 DELETE FROM public.user_role WHERE user_id=p_user_id AND role_id=p_role_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Assignment not found' USING ERRCODE='P0002'; END IF;
END $$;

CREATE PROCEDURE grant_role_permission(p_role_id integer,p_permission_id integer)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 PERFORM public.policy_lock();
 IF NOT EXISTS(SELECT 1 FROM public.role WHERE role_id=p_role_id) OR
    NOT EXISTS(SELECT 1 FROM public.permission WHERE permission_id=p_permission_id) THEN
  RAISE EXCEPTION 'Role or permission not found' USING ERRCODE='P0002'; END IF;
 INSERT INTO public.role_permission(role_id,permission_id) VALUES(p_role_id,p_permission_id);
END $$;

CREATE PROCEDURE revoke_role_permission(p_role_id integer,p_permission_id integer)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 PERFORM public.policy_lock();
 DELETE FROM public.role_permission WHERE role_id=p_role_id AND permission_id=p_permission_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Grant not found' USING ERRCODE='P0002'; END IF;
END $$;

CREATE PROCEDURE set_user_status(p_user_id integer,p_status varchar)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 PERFORM public.policy_lock();
 UPDATE public.app_user SET status=p_status WHERE user_id=p_user_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'User not found' USING ERRCODE='P0002'; END IF;
END $$;

CREATE PROCEDURE set_role_active(p_role_id integer,p_is_active boolean)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 PERFORM public.policy_lock();
 UPDATE public.role SET is_active=p_is_active WHERE role_id=p_role_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Role not found' USING ERRCODE='P0002'; END IF;
END $$;

CREATE PROCEDURE set_resource_active(p_resource_id integer,p_is_active boolean)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 PERFORM public.policy_lock();
 UPDATE public.resource SET is_active=p_is_active WHERE resource_id=p_resource_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Resource not found' USING ERRCODE='P0002'; END IF;
END $$;

CREATE PROCEDURE update_permission_identity(p_permission_id integer,p_resource_id integer,p_action_code varchar)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 PERFORM public.policy_lock();
 UPDATE public.permission SET resource_id=p_resource_id,action_code=p_action_code WHERE permission_id=p_permission_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'Permission not found' USING ERRCODE='P0002'; END IF;
END $$;
