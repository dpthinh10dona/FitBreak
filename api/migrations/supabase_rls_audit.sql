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
  owner_col TEXT;
  tables TEXT[] := ARRAY['profiles', 'vitals', 'workouts', 'health_states', 'user_schedules'];
BEGIN
  FOREACH tbl IN ARRAY tables LOOP
    IF EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = 'public' AND table_name = tbl
    ) THEN
      -- profiles is keyed by id; the remaining per-user tables use user_id.
      owner_col := CASE WHEN tbl = 'profiles' THEN 'id' ELSE 'user_id' END;
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = tbl AND column_name = owner_col
      ) THEN
        RAISE EXCEPTION 'Missing owner column %.%', tbl, owner_col;
      END IF;
      -- Bắt buộc bật RLS
      EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', tbl);

      -- Xóa policy cũ nếu đã tồn tại để tránh trùng lặp
      EXECUTE format('DROP POLICY IF EXISTS %I_select_own ON public.%I;', tbl, tbl);
      EXECUTE format('DROP POLICY IF EXISTS %I_insert_own ON public.%I;', tbl, tbl);
      EXECUTE format('DROP POLICY IF EXISTS %I_update_own ON public.%I;', tbl, tbl);
      EXECUTE format('DROP POLICY IF EXISTS %I_delete_own ON public.%I;', tbl, tbl);

      -- Tạo 4 Policy chặt chẽ với điều kiện auth.uid() = user_id
      EXECUTE format(
        'CREATE POLICY %I_select_own ON public.%I FOR SELECT USING (auth.uid() = %I);',
        tbl, tbl, owner_col
      );
      EXECUTE format(
        'CREATE POLICY %I_insert_own ON public.%I FOR INSERT WITH CHECK (auth.uid() = %I);',
        tbl, tbl, owner_col
      );
      EXECUTE format(
        'CREATE POLICY %I_update_own ON public.%I FOR UPDATE USING (auth.uid() = %I) WITH CHECK (auth.uid() = %I);',
        tbl, tbl, owner_col, owner_col
      );
      EXECUTE format(
        'CREATE POLICY %I_delete_own ON public.%I FOR DELETE USING (auth.uid() = %I);',
        tbl, tbl, owner_col
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
