create table mobile_answers (
  id uuid default gen_random_uuid() primary key,
  submitted_at timestamp with time zone default now(),
  session_id text,
  answers jsonb not null
);
