network = {
    'Catalyst':    {'comm_rate': .35, 'override_rate': 0,   'level': 1},
    'Visionary':   {'comm_rate': .4,  'override_rate': .05,'level': 2},
    'Trailblazer': {'comm_rate': .4,  'override_rate': .05,'level': 3},
}

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

def compute_commissions(df):
    df = calculate_OverrideSales(df)
    df['CommissionRate']     = df['Role'].map(lambda r: network[r]['comm_rate'])
    df['OverrideRate']     = df['Role'].map(lambda r: network[r]['override_rate'])
    df['PersonalComm'] = df['Sales'] * df['CommissionRate']
    df['OverrideComm'] = df['OverrideSales'] * df['OverrideRate']
    return df 