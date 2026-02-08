CREATE TABLE IF NOT EXISTS public.users (
    user_id text NOT NULL,
    username text UNIQUE,
    hashed_password text NOT NULL,
    key_salt text,
    fullname text NOT NULL,
    email text UNIQUE,
    scopes text array NOT NULL DEFAULT ARRAY['users:default'],
    is_banned boolean NOT NULL DEFAULT false,
    is_admin boolean NOT NULL DEFAULT false,
    CONSTRAINT users_pkey PRIMARY KEY (user_id)
);

CREATE TABLE IF NOT EXISTS public.urls (
    url_id serial PRIMARY KEY,
    url_key text UNIQUE,
    secret_key text UNIQUE,
    target_url text NOT NULL,
    is_active boolean NOT NULL DEFAULT true,
    clicks int8 NOT NULL DEFAULT 0,
    created_at timestamp NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    tags JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    notes_tsv tsvector -- Full-text search column
);

CREATE INDEX IF NOT EXISTS idx_notes_tsv ON notes USING GIN(notes_tsv);

-- Trigger function to update notes_tsv automatically
CREATE OR REPLACE FUNCTION public.update_notes_tsv() RETURNS trigger AS $$
BEGIN
  NEW.notes_tsv :=
    to_tsvector('english',
      coalesce(NEW.title,'') || ' ' || coalesce(NEW.content,'') || ' ' ||
      coalesce(NEW.slug,'')
    );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic tsvector update
CREATE TRIGGER notes_tsv_trigger
BEFORE INSERT OR UPDATE ON notes
FOR EACH ROW EXECUTE FUNCTION public.update_notes_tsv();

-- create admin user that is the default user for API
-- password is "weakadmin", update it!

INSERT INTO users VALUES (
    '01H8YA58JAE536F5XGMBM5NGMX',
    'admin',
    '$2b$12$Z4iAVlsZe2NY7rMxXkODjO2TZGmSJ/m4OQMGDWVw/gxy2JAsAYQ66',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjAxSDhZQTU4SkFFNTM2RjVYR01CTTVOR01YIiwiZ3JhbnRfdHlwZSI6InJlZnJlc2hfdG9rZW4iLCJleHBpcmF0aW9uIjoxNjkzNzU2NzA0LjgyNzI1LCJzYWx0IjoiQ1ZaOHVjbXBtRFQza2ZFTWZZZVQtZyJ9.x9CpuPo5H6bkF3CAE_Oeo8fJ3XGHUk4DB0XXBAYRiaM',
    'Mr. Admin',
    'admin@localhost',
    ARRAY ['admin'],
    false,
    true
) ON CONFLICT DO NOTHING; -- only insert if not exists
-- password for the user is "weakadmin", update it!