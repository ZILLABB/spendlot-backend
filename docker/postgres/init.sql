-- Create database if it doesn't exist
CREATE DATABASE spendlot;

-- Create user if it doesn't exist
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'spendlot_user') THEN

      CREATE ROLE spendlot_user LOGIN PASSWORD 'spendlot_password';
   END IF;
END
$do$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE spendlot TO spendlot_user;

-- Connect to the database
\c spendlot;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO spendlot_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO spendlot_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO spendlot_user;
