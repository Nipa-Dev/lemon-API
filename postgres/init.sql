CREATE TABLE IF NOT EXISTS public.users (
    user_id text NOT NULL,
    username text UNIQUE,
    hashed_password text NOT NULL,
    key_salt text,
    fullname text NOT NULL,
    email text UNIQUE,
    scopes text array NOT NULL DEFAULT ARRAY['users:read'],
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
    DEFAULT,
    DEFAULT
) ON CONFLICT DO NOTHING; -- only insert if not exists
-- password for the user is "weakadmin", update it!