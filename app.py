import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

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
    df = pd.read_excel(uploaded)
    st.subheader("Raw Data")
    st.dataframe(df)

    if st.button("Compute Commissions"):
        with st.spinner("Calculating…"):
            result = compute_commissions(df)
        st.success("Done!")
        st.subheader("With Commissions")
        st.dataframe(result)

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
