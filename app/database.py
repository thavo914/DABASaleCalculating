import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

def get_connection():
    """Establishes and returns a connection to the PostgreSQL database."""
    conn = psycopg2.connect(
        dbname=os.environ.get("POSTGRES_DB"),
        user=os.environ.get("POSTGRES_USER"),
        password=os.environ.get("POSTGRES_PASSWORD"),
        host=os.environ.get("POSTGRES_HOST"),
        port=os.environ.get("POSTGRES_PORT"),
        sslmode="require",
        gssencmode="disable"
    )
    return conn 