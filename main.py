import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from database import get_connection
from commission import compute_commissions
from ui import paginated_dataframe


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

# File uploader
uploaded = st.file_uploader("Upload your sales Excel", type=['xlsx','xls'])
if uploaded:
    df_sales = pd.read_excel(uploaded)
    st.subheader("Sales Data")
    paginated_dataframe(df_sales, "sales_page")

    if st.button("Compute Commissions"):
        with st.spinner("Calculating…"):
            try:
                df_merged = pd.merge(
                    df_customers,
                    df_sales,
                    on="CustomerCode",
                    how="inner",
                    suffixes=("_cust","_sales")
                    # (each customer can have multiple sales rows; you can also use "one_to_one" or "many_to_many")
                )
                # st.dataframe(df_merged)
                # df_final = (
                # df_merged
                # [["CustomerCode","FullName_cust", "Role_cust", "SuperiorCode_cust","Sales"]]
                # .rename(columns={
                #     "FullName_cust":"FullName",
                #     "Role_cust":"Role",
                #     "SuperiorCode_cust":"SuperiorCode",
                # })
                # )
                # st.dataframe(df_merged)
            except Exception as e:
                st.error(f"Error loading data from GitHub: {str(e)}")
            result = compute_commissions(df_merged)
        st.success("Done!")
        st.subheader("With Commissions")
        paginated_dataframe(result, "result_page")

        # — Download button —
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            result.to_excel(writer, index=False, sheet_name="Commissions")
            writer.close()
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
