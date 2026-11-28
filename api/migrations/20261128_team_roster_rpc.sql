-- Return a team's public roster without weakening the owner-only RLS policies
-- on profiles or stats. Run after supabase_rls_audit.sql.
CREATE OR REPLACE FUNCTION public.get_my_team_roster()
RETURNS TABLE (id uuid, nickname text, goal text)
LANGUAGE sql
STABLE
SECURITY DEFINER
SET search_path = public
AS $$
  WITH caller_team AS (
    SELECT s.team
    FROM public.stats AS s
    WHERE s.user_id = auth.uid()
      AND s.team IS NOT NULL
    LIMIT 1
  )
  SELECT p.id, p.nickname, p.goal
  FROM public.profiles AS p
  INNER JOIN public.stats AS member_stats ON member_stats.user_id = p.id
  INNER JOIN caller_team ON caller_team.team = member_stats.team
  ORDER BY p.nickname NULLS LAST, p.id;
$$;

REVOKE ALL ON FUNCTION public.get_my_team_roster() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_my_team_roster() TO authenticated;

NOTIFY pgrst, 'reload schema';
