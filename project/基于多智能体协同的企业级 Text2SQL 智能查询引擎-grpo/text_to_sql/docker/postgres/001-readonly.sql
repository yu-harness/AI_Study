DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'text2sql_readonly') THEN
        CREATE ROLE text2sql_readonly WITH LOGIN PASSWORD 'text2sql_readonly';
    END IF;
END
$$;

ALTER ROLE text2sql_readonly SET default_transaction_read_only = on;
GRANT CONNECT ON DATABASE text2sql TO text2sql_readonly;
GRANT USAGE ON SCHEMA public TO text2sql_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO text2sql_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE text2sql IN SCHEMA public
    GRANT SELECT ON TABLES TO text2sql_readonly;
