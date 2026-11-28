-- Apply on a reviewed Supabase database after backing up existing profile data.
-- Auth email remains in Supabase Auth because email/password login still requires it.
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS nickname text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS birth_year integer;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS allergies text[];
UPDATE public.profiles SET birth_year = extract(year FROM current_date)::integer - age
WHERE birth_year IS NULL AND age IS NOT NULL;
ALTER TABLE public.profiles ADD CONSTRAINT birth_year_valid CHECK (
  birth_year IS NULL OR birth_year BETWEEN 1900 AND extract(year FROM current_date)::integer - 12
);
UPDATE public.profiles SET nickname = 'Chiến binh'
WHERE nickname IS NULL OR btrim(nickname) = '';
ALTER TABLE public.profiles ALTER COLUMN nickname SET NOT NULL;
ALTER TABLE public.profiles ADD CONSTRAINT nickname_length CHECK (char_length(nickname) BETWEEN 1 AND 32);
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS status_flag text;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS status_note text;
ALTER TABLE public.profiles ADD CONSTRAINT status_flag_allowed CHECK (
  status_flag IS NULL OR status_flag IN
  ('restrict_heavy_exercise', 'maintain_activity', 'nutrition_review')
);

-- This existing field may contain earlier chat prose; clear it before the new flow.
UPDATE public.profiles SET food_recommendation = NULL;
ALTER TABLE public.profiles DROP COLUMN IF EXISTS name;
ALTER TABLE public.profiles DROP COLUMN IF EXISTS age;
ALTER TABLE public.profiles DROP COLUMN IF EXISTS email;
ALTER TABLE public.profiles DROP COLUMN IF EXISTS phone;
ALTER TABLE public.profiles DROP COLUMN IF EXISTS address;
ALTER TABLE public.profiles DROP COLUMN IF EXISTS school;
ALTER TABLE public.profiles DROP COLUMN IF EXISTS workplace;
ALTER TABLE public.stats DROP COLUMN IF EXISTS email;
ALTER TABLE public.raid ADD COLUMN IF NOT EXISTS invite_code uuid DEFAULT gen_random_uuid();
UPDATE public.raid SET invite_code = gen_random_uuid() WHERE invite_code IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS raid_invite_code_unique ON public.raid(invite_code);

-- Remove any legacy raw chat tables if they exist. Confirm table names before applying.
DROP TABLE IF EXISTS public.chat_history;
DROP TABLE IF EXISTS public.chat_messages;
