import psycopg2
from psycopg2 import OperationalError

def test_connection(dsn: str):
    try:
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()

        cur.execute("SELECT NOW();")
        now = cur.fetchone()[0]
        print("Current time on server:", now)

        cur.close()
        conn.close()
        print("✅ Connection successful!")
    except OperationalError as e:
        print("❌ Connection failed:", e)

if __name__ == "__main__":
    # Fill in your real password below
    dsn = (
        "postgresql://"
        "postgres.actwwlqzdzksadavdmyw:"
        "4WDOU8V5MWEt3PQj"
        "@aws-0-us-east-2.pooler.supabase.com:6543/postgres"
        "?sslmode=require"
        "&gssencmode=disable"
    )

    test_connection(dsn)
