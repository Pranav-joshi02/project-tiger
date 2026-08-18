import psycopg

def setup_postgres():
    conn = psycopg.connect('host=127.0.0.1 port=5432 user=postgres dbname=postgres', autocommit=True)
    with conn.cursor() as cur:
        # Create role pench
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'pench';")
        if not cur.fetchone():
            cur.execute("CREATE ROLE pench WITH LOGIN PASSWORD 'pench' SUPERUSER CREATEDB;")
            print("Created user 'pench'")
        else:
            cur.execute("ALTER ROLE pench WITH PASSWORD 'pench' SUPERUSER CREATEDB;")
            print("Updated user 'pench'")
            
        # Create database pench
        cur.execute("SELECT 1 FROM pg_database WHERE datname = 'pench';")
        if not cur.fetchone():
            cur.execute("CREATE DATABASE pench OWNER pench;")
            print("Created database 'pench'")
        else:
            print("Database 'pench' already exists")
    conn.close()

    # Connect to pench database
    conn_pench = psycopg.connect('host=127.0.0.1 port=5432 user=pench password=pench dbname=pench', autocommit=True)
    with conn_pench.cursor() as cur:
        # Try creating vector and postgis extensions if present
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            print("Vector extension enabled.")
        except Exception as e:
            print("Note on vector extension:", e)
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            print("PostGIS extension enabled.")
        except Exception as e:
            print("Note on postgis extension:", e)
    conn_pench.close()
    print("PostgreSQL setup completed successfully!")

if __name__ == "__main__":
    setup_postgres()
