import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
from database import get_sqlalchemy_engine
from sqlalchemy import text
import pandas as pd

st.title("👤 Customer Management")

# Add role ID legend

# Form for creating/updating customer
with st.form("customer_form"):
    customercode = st.text_input("Mã khách hàng")
    fullname = st.text_input("Tên khách hàng")
    roleid = st.number_input("Cấp bậc", min_value=1, step=1)
    st.caption("**Cấp bậc:** 1 = Catalyst, 2 = Visionary, 3 = Trailblazer, 4 = Agent, 5 = Agent 1, 6 = Agent 2, 7 = Agent 3, 8 = Agent 4, 9 = Agent 5")
    superiorcode = st.text_input("Mã quản lý", value="")
    submitted = st.form_submit_button("Lưu")

    if submitted:
        try:
            engine = get_sqlalchemy_engine()
            with engine.begin() as conn:
                # Check if customer code already exists
                existing_customer = pd.read_sql_query(
                    "SELECT customercode FROM public.customers WHERE customercode = :customercode", 
                    conn, 
                    params={"customercode": customercode}
                )
                
                if not existing_customer.empty:
                    st.error(f"Customer code '{customercode}' already exists in the database. Please use a different code.")
                else:
                    # Insert new customer
                    conn.execute(text("""
                        INSERT INTO public.customers (customercode, fullname, roleid, superiorcode)
                        VALUES (:customercode, :fullname, :roleid, :superiorcode)
                    """), {
                        "customercode": customercode,
                        "fullname": fullname,
                        "roleid": roleid,
                        "superiorcode": superiorcode or None
                    })
                    st.success("Customer saved successfully!")
        except Exception as e:
            st.error(f"Error: {e}")

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
            engine = get_sqlalchemy_engine()
            with engine.begin() as conn:
                # Get existing customer codes from database
                existing_codes = pd.read_sql_query(
                    "SELECT customercode FROM public.customers", 
                    conn
                )['customercode'].tolist()
                
                # Filter out duplicates
                new_customers = []
                duplicate_count = 0
                
                for _, row in df_import.iterrows():
                    if row["customercode"] not in existing_codes:
                        new_customers.append({
                            "customercode": row["customercode"],
                            "fullname": row["fullname"],
                            "roleid": role_name_to_id.get(str(row["role"]), None),
                            "superiorcode": row.get("superiorcode", None)
                        })
                    else:
                        duplicate_count += 1
                
                # Insert only new customers
                if new_customers:
                    for customer in new_customers:
                        conn.execute(text("""
                            INSERT INTO public.customers (customercode, fullname, roleid, superiorcode)
                            VALUES (:customercode, :fullname, :roleid, :superiorcode)
                        """), customer)
                
                # Show results
                if duplicate_count > 0:
                    st.warning(f"Found {duplicate_count} duplicate customer(s) that were skipped.")
                
                if new_customers:
                    st.success(f"Successfully imported {len(new_customers)} new customer(s)!")
                else:
                    st.info("No new customers to import - all were duplicates.")
    except Exception as e:
        st.error(f"Error importing customers: {e}")

# Show all customers
st.markdown("---")
st.subheader("Dữ liệu khách hàng")
try:
    engine = get_sqlalchemy_engine()
    df_customers = pd.read_sql_query("""
        SELECT c.customercode, c.fullname, r.rolename, c.superiorcode
        , c2.fullname AS superiorname
        FROM public.customers c
        INNER JOIN roles r ON c.roleid = r.id
        LEFT JOIN public.customers c2 ON c.superiorcode = c2.customercode
    ; """, engine)
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
except Exception as e:
    st.error(f"Error loading customers: {e}")
