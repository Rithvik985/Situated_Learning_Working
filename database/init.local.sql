-- Local initializer for Situated Learning DB (psql client required)
-- Safely creates role and database if they don't exist, then loads main schema.
-- Usage (run from repo root so the relative include works):
--   psql -U postgres -h localhost -f database/init.local.sql

\set ON_ERROR_STOP on

-- 1) Ensure we're connected to the default maintenance DB
\connect postgres

-- 2) Create role 'admin' if it doesn't exist (LOGIN with password)
SELECT 'CREATE ROLE admin LOGIN PASSWORD ''password1234''' 
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'admin');
\gexec

-- 3) Grant CREATEDB to admin (idempotent)
ALTER ROLE admin CREATEDB;

-- 4) Create database if it doesn't exist, owned by admin
SELECT 'CREATE DATABASE situated_learning_db OWNER admin TEMPLATE template0 ENCODING ''UTF8'' LC_COLLATE ''C'' LC_CTYPE ''C''' 
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'situated_learning_db');
\gexec

-- 5) Connect to the app database
\connect situated_learning_db admin

-- 6) Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 7) Load the main schema (relative to repo root)
\i ./database/init.sql
