import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from database import get_sqlalchemy_engine
from commission import compute_commissions, calculate_quarterly_bonus
from ui import paginated_dataframe
from pandas.tseries.offsets import MonthEnd
from datetime import datetime
import re


# --- Streamlit UI ---
st.title("💼 Sales & Commission Calculator")


# File uploader
uploaded = st.file_uploader("1. Import dữ liệu bán hàng", type=['xlsx','xls'])
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
selected_month = st.selectbox("2. Chọn doanh thu theo tháng", sorted(available_months))
engine = get_sqlalchemy_engine()

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

df_monthly_revenue = pd.read_sql_query(query, engine)
# Insert selectedmonth column by index
df_monthly_revenue.insert(0, 'selectedmonth', selected_month)
df_monthly_revenue_display = df_monthly_revenue.copy()
df_monthly_revenue_display['sales'] = df_monthly_revenue_display['sales'].apply(lambda x: f"{x:,.0f}")

st.data_editor(
    df_monthly_revenue_display,
    column_config={
        "customercode": st.column_config.Column(label="Mã khách hàng"),
        "fullname": st.column_config.Column(label="Tên khách hàng"),
        "rolename": st.column_config.Column(label="Cấp bậc"),
        "superiorcode": st.column_config.Column(label="Mã quản lý"),
        "superiorname": st.column_config.Column(label="Tên quản lý"),
        "selectedmonth": st.column_config.Column(label="Tháng"),
        "sales": st.column_config.Column(label="Doanh số cá nhân"),
    }
)



if st.button("Tính hoa hồng"):
    result = compute_commissions(df_monthly_revenue)

    result_display = result.copy()
    for col in ['sales', 'bonus_value', 'personalcomm', 'overridecomm']:
        if col in result_display.columns:
            result_display[col] = result_display[col].apply(lambda x: f"{x:,.0f}")

    result_column_aliases = {
    "customercode": "Mã khách hàng",
    "fullname": "Tên khách hàng",
    "rolename": "Cấp bậc",
    "superiorcode": "Mã quản lý",
    "superiorname": "Tên quản lý",
    "selectedmonth": "Tháng",
    "sales": "Doanh số",
    "overridesales": "Doanh số vượt cấp (từ cấp dưới)",
    "commissionrate": "Tỷ lệ hoa hồng",
    "overriderate": "Tỷ lệ hoa hồng vượt cấp",
    "personalcomm": "Hoa hồng cá nhân",
    "overridecomm": "Hoa hồng vượt cấp",
    }
    st.success("Done!")
    st.subheader("Hoa hồng theo hệ thống")
    paginated_dataframe(result_display, "result_page", column_aliases=result_column_aliases)

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

# Add single selectbox for quarter and year selection
current_year = datetime.now().year
year_range = range(current_year - 1, current_year + 2)  # last year to next year
quarter_options = [f"Q{q} {y}" for y in year_range for q in range(1, 5)]
selected_quarter_year = st.selectbox("3. Chọn quý và năm (Select Quarter and Year)", quarter_options)

# Parse selected_quarter_year to get start and end dates for the quarter
def get_quarter_date_range(selected_quarter_year):
    match = re.match(r"Q(\d) (\d{4})", selected_quarter_year)
    if not match:
        return None, None
    quarter = int(match.group(1))
    year = int(match.group(2))
    if quarter == 1:
        start_date = pd.Timestamp(year=year, month=1, day=1)
        end_date = pd.Timestamp(year=year, month=3, day=31)
    elif quarter == 2:
        start_date = pd.Timestamp(year=year, month=4, day=1)
        end_date = pd.Timestamp(year=year, month=6, day=30)
    elif quarter == 3:
        start_date = pd.Timestamp(year=year, month=7, day=1)
        end_date = pd.Timestamp(year=year, month=9, day=30)
    elif quarter == 4:
        start_date = pd.Timestamp(year=year, month=10, day=1)
        end_date = pd.Timestamp(year=year, month=12, day=31)
    else:
        return None, None
    return start_date, end_date

start_date, end_date = get_quarter_date_range(selected_quarter_year)
df_quarter = pd.DataFrame()
if start_date and end_date:
    # Filter df_monthly_revenue by selected quarter and year
    df_quarter = pd.read_sql_query(f"""
    SELECT c1.customercode,
        c1.fullname,
        r.rolename,
        SUM(s.revenue) as sales
    FROM public.sales s
            INNER JOIN public.customers c1 ON c1.customercode = s.customercode
            INNER JOIN public.roles r ON c1.roleid = r.id
    WHERE s.createddate >= '{start_date.strftime('%Y-%m-%d')}'
    AND s.createddate <= '{end_date.strftime('%Y-%m-%d')}'
    GROUP BY c1.customercode, c1.fullname, r.rolename
    """, engine)
    # Insert selectedmonth column by index
    df_quarter.insert(0, 'quarteryear', selected_quarter_year)
    df_quarter_display = df_quarter.copy()
    df_quarter_display['sales'] = df_quarter_display['sales'].apply(lambda x: f"{x:,.0f}")

    st.data_editor(
        df_quarter_display,
        column_config={
            "customercode": st.column_config.Column(label="Mã khách hàng"),
            "fullname": st.column_config.Column(label="Tên khách hàng"),
            "rolename": st.column_config.Column(label="Cấp bậc"),
            "quarteryear": st.column_config.Column(label="Quý"),
            "sales": st.column_config.Column(label="Doanh số"),
        }
    )
# Calculate and display quarterly bonus
    if st.button("Tính thưởng quý (Quarterly Bonus)"):

        df_with_bonus = calculate_quarterly_bonus(df_quarter)
        df_with_bonus_display = df_with_bonus.copy()
        for col in ['sales', 'bonus_value']:
            if col in df_with_bonus_display.columns:
                df_with_bonus_display[col] = df_with_bonus_display[col].apply(lambda x: f"{x:,.0f}")
        st.success("Done!")
        st.subheader(f"Thưởng quý theo doanh số - {selected_quarter_year}")
        result_column_aliases = {
        "quarteryear": "Quý",
        "customercode": "Mã khách hàng",
        "fullname": "Tên khách hàng",
        "rolename": "Cấp bậc",
        "superiorcode": "Mã quản lý",
        "superiorname": "Tên quản lý",
        "selectedmonth": "Tháng",
        "sales": "Doanh số theo quý",
        "bonus_percentage": "Tỉ lệ thưởng quý",
        "bonus_value": "Số tiền thưởng",
        }
        paginated_dataframe(df_with_bonus_display, "result_page", column_aliases=result_column_aliases)
        # Download button for bonus results
        buffer_bonus = BytesIO()
        df_with_bonus.to_excel(buffer_bonus, index=False, sheet_name="QuarterlyBonus", engine="openpyxl")
        buffer_bonus.seek(0)
        st.download_button(
            label="📥 Download quarterly bonus as Excel",
            data=buffer_bonus,
            file_name=f"quarterly_bonus_{selected_quarter_year.replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )