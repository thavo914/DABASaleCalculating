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


# --- Streamlit UI ---
st.title("💼 Sales & Commission Calculator")


# File uploader
uploaded = st.file_uploader("Upload your sales Excel", type=['xlsx','xls'])
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



        # # — Download button —
        # buffer = BytesIO()
        # result.to_excel(buffer, index=False, sheet_name="Commissions", engine="openpyxl")
        # buffer.seek(0)

        # st.download_button(
        #     label="📥 Download results as Excel",
        #     data=buffer,
        #     file_name="commission_results.xlsx",
        #     mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        # )

        # Summary metrics
        # total_sales   = result['Sales'].sum()
        # total_override= result['OverrideSales'].sum()
        # total_comm    = result['PersonalComm'].sum() + result['OverrideComm'].sum()
        # st.markdown(f"""
        # **System Sales:** {total_sales:,.0f}  
        # **System Override Base:** {total_override:,.0f}  
        # **Total Payout (comm+override):** {total_comm:,.0f}
        # """)

        # Simple bar chart of commissions by Role
        # fig, ax = plt.subplots()
        # summary = result.groupby('Role')[['PersonalComm','OverrideComm']].sum()
        # summary.plot.bar(ax=ax)
        # ax.set_ylabel("Commission Amount")
        # ax.set_title("Commission by Role")
        # st.pyplot(fig)


# Sample data
df_sales = pd.DataFrame({
    "createddate": ["2024-05-01", "2024-05-15", "2024-06-10", "2024-06-20"]
})

# Convert to datetime
df_sales["createddate"] = pd.to_datetime(df_sales["createddate"])

# Create year_month column
df_sales["year_month"] = df_sales["createddate"].dt.to_period("M")

available_months = df_sales["year_month"].astype(str).unique()
selected_month = st.selectbox("Select month", sorted(available_months, reverse=True))

