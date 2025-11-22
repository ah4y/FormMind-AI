-- Init DB schema for FormMind
-- Run this file against a PostgreSQL database to create tables

CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    password_hash TEXT,
    role TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS forms (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'draft',
    access_type TEXT NOT NULL DEFAULT 'public',
    single_submission BOOLEAN DEFAULT FALSE,
    submission_start TIMESTAMP WITH TIME ZONE,
    submission_end TIMESTAMP WITH TIME ZONE,
    public_token TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS form_versions (
    id SERIAL PRIMARY KEY,
    form_id INTEGER REFERENCES forms(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    form_version_id INTEGER REFERENCES form_versions(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    placeholder TEXT,
    help_text TEXT,
    field_type TEXT,
    required BOOLEAN DEFAULT FALSE,
    default_value TEXT,
    order_index INTEGER DEFAULT 0,
    validation_min NUMERIC,
    validation_max NUMERIC,
    validation_regex TEXT
);

CREATE TABLE IF NOT EXISTS question_options (
    id SERIAL PRIMARY KEY,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    label TEXT,
    value TEXT,
    order_index INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    form_id INTEGER REFERENCES forms(id) ON DELETE CASCADE,
    form_version_id INTEGER REFERENCES form_versions(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    guest_token TEXT,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completion_time_ms INTEGER
);

CREATE TABLE IF NOT EXISTS answers (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER REFERENCES submissions(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(id) ON DELETE CASCADE,
    value TEXT
);

CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT,
    visibility TEXT DEFAULT 'private',
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);
