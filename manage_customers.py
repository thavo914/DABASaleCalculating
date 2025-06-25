import streamlit as st
import psycopg2
from src.database import get_connection
import pandas as pd

st.title("👤 Customer Management")

# Add role ID legend

# Form for creating/updating customer
with st.form("customer_form"):
    customercode = st.text_input("Mã khách hàng")
    fullname = st.text_input("Tên khách hàng")
    roleid = st.number_input("Cấp bậc", min_value=1, step=1)
    st.caption("**Cấp bậc:** 1 = Catalyst, 2 = Visionary, 3 = Trailblazer")
    superiorcode = st.text_input("Mã quản lý", value="")
    submitted = st.form_submit_button("Lưu")

    if submitted:
        try:
            conn = get_connection()
            cur = conn.cursor()
            # Upsert logic: update if exists, else insert
            cur.execute("""
                INSERT INTO public.customers (customercode, fullname, roleid, superiorcode)
                VALUES (%s, %s, %s, %s)
            """, (customercode, fullname, roleid, superiorcode or None))
            conn.commit()
            st.success("Customer saved successfully!")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            cur.close()
            conn.close()

st.markdown("---")
st.subheader("Import Customers from Excel")

uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])

role_name_to_id = {
    "Catalyst": 1,
    "Visionary": 2,
    "Trailblazer": 3
}

if uploaded_file:
    try:
        df_import = pd.read_excel(uploaded_file)
        st.dataframe(df_import)  # Preview the data

        if st.button("Import Customers"):
            conn = get_connection()
            cur = conn.cursor()
            for _, row in df_import.iterrows():
                cur.execute("""
                    INSERT INTO public.customers (customercode, fullname, roleid, superiorcode)
                    VALUES (%s, %s, %s, %s)
                """, (
                    row["customercode"],
                    row["fullname"],
                    role_name_to_id.get(str(row["role"]), None),
                    row.get("superiorcode", None)
                ))
            conn.commit()
            cur.close()
            conn.close()
            st.success("Customers imported successfully!")
    except Exception as e:
        st.error(f"Error importing customers: {e}")

# Show all customers
st.markdown("---")
st.subheader("Dữ liệu khách hàng")
try:
    conn = get_connection()
    df_customers = pd.read_sql_query("""
        SELECT c.customercode, c.fullname, r.rolename, c.superiorcode
        , c2.fullname AS superiorname
        FROM public.customers c
        INNER JOIN roles r ON c.roleid = r.id
        LEFT JOIN public.customers c2 ON c.superiorcode = c2.customercode
    ; """, conn)
    st.data_editor(
        df_customers,
        column_config={
            "customercode": st.column_config.Column(label="Mã khách hàng"),
            "fullname": st.column_config.Column(label="Tên khách hàng"),
            "rolename": st.column_config.Column(label="Cấp bậc"),
            "superiorcode": st.column_config.Column(label="Mã quản lý"),
            "superiorname": st.column_config.Column(label="Tên quản lý"),
        }
    )
    conn.close()
except Exception as e:
    st.error(f"Error loading customers: {e}")
