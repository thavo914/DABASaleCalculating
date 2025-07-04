import os
import psycopg2
from dotenv import load_dotenv
import streamlit as st
from sqlalchemy import create_engine
load_dotenv()  # Load variables from .env file

# def get_connection():
#     """Establishes and returns a connection to the PostgreSQL database using Streamlit secrets."""
#     conn = psycopg2.connect(
#         dbname=st.secrets["POSTGRES_DB"],
#         user=st.secrets["POSTGRES_USER"],
#         password=st.secrets["POSTGRES_PASSWORD"],
#         host=st.secrets["POSTGRES_HOST"],
#         port=st.secrets["POSTGRES_PORT"],
#         sslmode="require",
#         gssencmode="disable"
#     )
#     return conn 


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

def get_sqlalchemy_engine():
    """
    Returns a SQLAlchemy engine for PostgreSQL using environment variables.
    """
    user = os.environ.get("POSTGRES_USER")
    password = os.environ.get("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST")
    port = os.environ.get("POSTGRES_PORT")
    db = os.environ.get("POSTGRES_DB")
    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}?sslmode=require&gssencmode=disable"
    ) 