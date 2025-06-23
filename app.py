import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import requests
import tempfile
from io import BytesIO

@st.cache_resource
def get_connection():
    url = "https://raw.githubusercontent.com/thavo914/DABASaleCalculating/main/sales.db"
    r = requests.get(url)
    r.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.write(r.content)
    tmp.flush()
    return sqlite3.connect(tmp.name, check_same_thread=False)

# --- Your commission logic ---
def calculate_OverrideSales(df):
    df['OverrideSales'] = 0
    for role in ['Catalyst', 'Visionary', 'Trailblazer']:
        role_staff = df[df['Role'] == role]
        for _, staff in role_staff.iterrows():
            subs = df['SuperiorCode'] == staff['CustomerCode']
            subordinate_sales = df.loc[subs, 'Sales'].sum()
            subordinate_override = df.loc[subs, 'OverrideSales'].sum()
            total_override = subordinate_sales + subordinate_override
            df.loc[df['CustomerCode'] == staff['CustomerCode'], 'OverrideSales'] = total_override
    return df

network = {
    'Catalyst':    {'comm_rate': .35, 'override_rate': 0,   'level': 1},
    'Visionary':   {'comm_rate': .4,  'override_rate': .05,'level': 2},
    'Trailblazer': {'comm_rate': .4,  'override_rate': .05,'level': 3},
}

def compute_commissions(df):
    df = calculate_OverrideSales(df)
    df['CommissionRate']     = df['Role'].map(lambda r: network[r]['comm_rate'])
    df['OverrideRate']     = df['Role'].map(lambda r: network[r]['override_rate'])
    df['PersonalComm'] = df['Sales'] * df['CommissionRate']
    df['OverrideComm'] = df['OverrideSales'] * df['OverrideRate']
    return df


# --- Streamlit UI ---
st.title("💼 Sales & Commission Calculator")

# File uploader
uploaded = st.file_uploader("Upload your sales Excel", type=['xlsx','xls'])
if uploaded:
    df_sales = pd.read_excel(uploaded)
    st.subheader("Sales Data")
    st.dataframe(df_sales)

    if st.button("Compute Commissions"):
        with st.spinner("Calculating…"):
            try:
                conn = get_connection()
                df_customers = pd.read_sql_query("SELECT * FROM customers", conn)
                st.subheader("Customer Data")
                st.dataframe(df_customers)
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
        st.dataframe(result)

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
