import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from database import get_connection
from commission import compute_commissions
from ui import paginated_dataframe
import psycopg2


# --- Streamlit UI ---
st.title("💼 Sales & Commission Calculator")

conn = get_connection()
df_customers = pd.read_sql_query("""
    SELECT c.customercode, c.fullname, r.rolename, c.superiorcode
    , c2.fullname AS superiorname
    FROM public.customers c
    INNER JOIN roles r ON c.roleid = r.id
    LEFT JOIN public.customers c2 ON c.superiorcode = c2.customercode
; """, conn)
st.subheader("Dữ liệu khách hàng")
customer_column_aliases = {
    "customercode": "Mã khách hàng",
    "fullname": "Tên khách hàng",
    "rolename": "Cấp bậc",
    "superiorcode": "Mã quản lý",
    "superiorname": "Tên quản lý"
}
paginated_dataframe(df_customers, "customer_page", column_aliases=customer_column_aliases)
st.markdown('[🌐 Visit Google](https://www.google.com)')

# File uploader
uploaded = st.file_uploader("Upload your sales Excel", type=['xlsx','xls'])
if uploaded:
    df_sales = pd.read_excel(uploaded)
    st.subheader("Sales Data")
    st.dataframe(df_sales)

    if st.button("Compute Commissions"):
        with st.spinner("Calculating…"):
            try:
                df_merged = pd.merge(
                    df_customers,
                    df_sales,
                    on="customercode",
                    how="inner",
                    suffixes=("_cust","_sales")
                )

            except Exception as e:
                st.error(f"Error loading data from GitHub: {str(e)}")
            result = compute_commissions(df_merged)
        st.success("Done!")
        st.subheader("With Commissions")
        paginated_dataframe(result, "result_page")

        # — Download button —
        buffer = BytesIO()
        result.to_excel(buffer, index=False, sheet_name="Commissions", engine="openpyxl")
        buffer.seek(0)

        st.download_button(
            label="📥 Download results as Excel",
            data=buffer,
            file_name="commission_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Summary metrics
        total_sales   = result['Sales'].sum()
        total_override= result['OverrideSales'].sum()
        total_comm    = result['PersonalComm'].sum() + result['OverrideComm'].sum()
        st.markdown(f"""
        **System Sales:** {total_sales:,.0f}  
        **System Override Base:** {total_override:,.0f}  
        **Total Payout (comm+override):** {total_comm:,.0f}
        """)

        # Simple bar chart of commissions by Role
        fig, ax = plt.subplots()
        summary = result.groupby('Role')[['PersonalComm','OverrideComm']].sum()
        summary.plot.bar(ax=ax)
        ax.set_ylabel("Commission Amount")
        ax.set_title("Commission by Role")
        st.pyplot(fig)

st.title("👤 Customer Management")

# Form for creating/updating customer
with st.form("customer_form"):
    customercode = st.text_input("Customer Code")
    fullname = st.text_input("Full Name")
    roleid = st.number_input("Role ID", min_value=1, step=1)
    superiorcode = st.text_input("Superior Code (optional)", value="")
    submitted = st.form_submit_button("Save Customer")

    if submitted:
        try:
            conn = get_connection()
            cur = conn.cursor()
            # Upsert logic: update if exists, else insert
            cur.execute("""
                INSERT INTO public.customers (customercode, fullname, roleid, superiorcode)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (customercode) DO UPDATE
                SET fullname=EXCLUDED.fullname, roleid=EXCLUDED.roleid, superiorcode=EXCLUDED.superiorcode
            """, (customercode, fullname, roleid, superiorcode or None))
            conn.commit()
            st.success("Customer saved successfully!")
        except Exception as e:
            st.error(f"Error: {e}")
        finally:
            cur.close()
            conn.close()

# Show all customers
st.markdown("---")
st.subheader("All Customers")
try:
    conn = get_connection()
    df = st.experimental_data_editor(
        st.dataframe(
            pd.read_sql_query("SELECT * FROM public.customers", conn)
        )
    )
    conn.close()
except Exception as e:
    st.error(f"Error loading customers: {e}")

