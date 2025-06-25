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
from pandas.tseries.offsets import MonthEnd
from datetime import datetime


# --- Streamlit UI ---
st.title("💼 Sales & Commission Calculator")


# File uploader
uploaded = st.file_uploader("Import dữ liệu bán hàng", type=['xlsx','xls'])
if uploaded:
    df_sales = pd.read_excel(uploaded)
    st.subheader("Sales Data")
    st.dataframe(df_sales)
    rename_map = {
        str(df_sales.columns[0]): "customercode",
        str(df_sales.columns[11]): "ordercode",
        str(df_sales.columns[12]): "createddate",
        str(df_sales.columns[13]): "staffname",
        str(df_sales.columns[15]): "totalprice",
        str(df_sales.columns[16]): "discountvalue",
        str(df_sales.columns[17]): "revenue",

    }
    df_sales.rename(columns=rename_map, inplace=True)
    st.dataframe(df_sales)

    if st.button("Import Sales Data"):
        try:
            conn = get_connection()
            cur = conn.cursor()
            for _, row in df_sales.iterrows():
                cur.execute("""
                    INSERT INTO Sales (customercode, ordercode, createddate, staffname, totalprice, discountvalue, revenue)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    row["customercode"],
                    row["ordercode"],
                    row["createddate"],
                    row["staffname"],
                    row["totalprice"],
                    row["discountvalue"],
                    row["revenue"]
                ))
            conn.commit()
            cur.close()
            conn.close()
            st.success("Sales data imported successfully!")
        except Exception as e:
            st.error(f"Error importing sales data: {e}")


        # Simple bar chart of commissions by Role
        # fig, ax = plt.subplots()
        # summary = result.groupby('Role')[['PersonalComm','OverrideComm']].sum()
        # summary.plot.bar(ax=ax)
        # ax.set_ylabel("Commission Amount")
        # ax.set_title("Commission by Role")
        # st.pyplot(fig)


# Sample data
now = pd.Timestamp(datetime.now().replace(day=1))
dates = pd.date_range(start=now - pd.DateOffset(months=4), periods=9, freq="MS")
df_sales = pd.DataFrame({
    "createddate": dates
})

# Convert to datetime
df_sales["createddate"] = pd.to_datetime(df_sales["createddate"])

# Create year_month column
df_sales["year_month"] = df_sales["createddate"].dt.to_period("M")

available_months = df_sales["year_month"].astype(str).unique()
selected_month = st.selectbox("Chọn doanh thu theo tháng", sorted(available_months))
conn = get_connection()

# After selected_month is set
# Convert selected_month (e.g., "2024-06") to start and end dates
start_date = pd.Period(selected_month).start_time
end_date = pd.Period(selected_month).end_time

query = f"""
SELECT c1.customercode,
       c1.fullname,
       r.rolename,
       c1.superiorcode,
       c2.fullname    AS superiorname,
       SUM(s.revenue) as sales
FROM public.sales s
         INNER JOIN public.customers c1 ON c1.customercode = s.customercode
         INNER JOIN public.roles r ON c1.roleid = r.id
         LEFT JOIN public.customers c2 ON c1.superiorcode = c2.customercode
WHERE s.createddate >= '{start_date}'
  AND s.createddate <= '{end_date}'
GROUP BY c1.customercode, c1.fullname, r.rolename, c1.superiorcode, c2.fullname
"""

df_monthly_revenue = pd.read_sql_query(query, conn)

st.data_editor(
        df_monthly_revenue,
        column_config={
            "customercode": st.column_config.Column(label="Mã khách hàng"),
            "fullname": st.column_config.Column(label="Tên khách hàng"),
            "rolename": st.column_config.Column(label="Cấp bậc"),
            "superiorcode": st.column_config.Column(label="Mã quản lý"),
            "superiorname": st.column_config.Column(label="Tên quản lý"),
            "sales": st.column_config.Column(label="Doanh số"),
        }
    )

if st.button("Tính hoa hồng"):
    result = compute_commissions(df_monthly_revenue)
    result_column_aliases = {
    "customercode": "Mã khách hàng",
    "fullname": "Tên khách hàng",
    "rolename": "Cấp bậc",
    "superiorcode": "Mã quản lý",
    "superiorname": "Tên quản lý",
    "sales": "Doanh số",

}
    st.success("Done!")
    st.subheader("Hoa hồng theo hệ thống")
    paginated_dataframe(result, "result_page", column_aliases=result_column_aliases)

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
    total_sales   = result['sales'].sum()
    total_override= result['overridesales'].sum()
    total_comm    = result['personalcomm'].sum() + result['overridecomm'].sum()
    st.markdown(f"""
    **System Sales:** {total_sales:,.0f}  
    **System Override Base:** {total_override:,.0f}  
    **Total Payout (comm+override):** {total_comm:,.0f}
    """)