# app.py
import streamlit as st
import sqlite3
import pandas as pd
import requests
import tempfile

@st.cache_resource
def get_connection():
    url = "https://raw.githubusercontent.com/thavo914/DABASaleCalculating/main/sales.db"
    r   = requests.get(url)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.write(r.content)
    tmp.flush()
    return sqlite3.connect(tmp.name, check_same_thread=False)

@st.cache_data
def load_customers() -> pd.DataFrame:
    conn = get_connection()
    return pd.read_sql_query("SELECT * FROM customers", conn)

def main():
    st.title("🗄️ Customers from sales.db")
    df = load_customers()
    st.subheader("All Customers")
    st.dataframe(df)

    st.subheader("🔍 Run Ad-Hoc SQL")
    sql = st.text_area(
        "Enter a SELECT query",
        value="SELECT * FROM customers LIMIT 5;"
    )
    if st.button("Run"):
        try:
            conn = get_connection()
            df_q = pd.read_sql_query(sql, conn)
            st.success(f"Returned {len(df_q)} rows")
            st.dataframe(df_q)
        except Exception as e:
            st.error(f"Query failed: {e}")

if __name__ == "__main__":
    main()
