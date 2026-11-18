create index if not exists sesm_students_reviewed_by_idx on public.sesm_students(reviewed_by) where reviewed_by is not null;
