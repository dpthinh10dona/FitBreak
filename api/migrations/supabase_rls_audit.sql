-- ============================================================================
-- SUPABASE ROW LEVEL SECURITY (RLS) AUDIT & ENFORCEMENT SCRIPT
-- FitBreak - Privacy & Data Isolation (auth.uid() = user_id)
-- ============================================================================

-- 1. Kiểm tra trạng thái RLS hiện tại của các bảng trong schema public
SELECT
  schemaname,
  tablename,
  rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('profiles', 'vitals', 'workouts', 'health_states', 'user_schedules')
ORDER BY tablename;

-- 2. Bật RLS & thiết lập Policy (SELECT, INSERT, UPDATE, DELETE) cho từng bảng
DO $$
DECLARE
  tbl TEXT;
  tables TEXT[] := ARRAY['profiles', 'vitals', 'workouts', 'health_states', 'user_schedules'];
BEGIN
  FOREACH tbl IN ARRAY tables LOOP
    IF EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name = tbl
    ) THEN
      -- Bắt buộc bật RLS
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', tbl);

      -- Xóa policy cũ nếu đã tồn tại để tránh trùng lặp
      EXECUTE format('DROP POLICY IF EXISTS %I_select_own ON public.%I;', tbl, tbl);
      EXECUTE format('DROP POLICY IF EXISTS %I_insert_own ON public.%I;', tbl, tbl);
      EXECUTE format('DROP POLICY IF EXISTS %I_update_own ON public.%I;', tbl, tbl);
      EXECUTE format('DROP POLICY IF EXISTS %I_delete_own ON public.%I;', tbl, tbl);

      -- Tạo 4 Policy chặt chẽ với điều kiện auth.uid() = user_id
      EXECUTE format(
        'CREATE POLICY %I_select_own ON public.%I FOR SELECT USING (auth.uid() = user_id);',
        tbl, tbl
      );
      EXECUTE format(
        'CREATE POLICY %I_insert_own ON public.%I FOR INSERT WITH CHECK (auth.uid() = user_id);',
        tbl, tbl
      );
      EXECUTE format(
        'CREATE POLICY %I_update_own ON public.%I FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);',
        tbl, tbl
      );
      EXECUTE format(
        'CREATE POLICY %I_delete_own ON public.%I FOR DELETE USING (auth.uid() = user_id);',
        tbl, tbl
      );
    END IF;
  END LOOP;
END $$;

-- 3. Liệt kê toàn bộ Policy đang áp dụng để kiểm tra
SELECT
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('profiles', 'vitals', 'workouts', 'health_states', 'user_schedules')
ORDER BY tablename, cmd;
