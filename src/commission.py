network = {
    'Catalyst':    {'comm_rate': .35, 'override_rate': 0,   'level': 1},
    'Visionary':   {'comm_rate': .4,  'override_rate': .05,'level': 2},
    'Trailblazer': {'comm_rate': .4,  'override_rate': .05,'level': 3},
}

def calculate_OverrideSales(df):
    df['overridesales'] = 0
    for role in ['Catalyst', 'Visionary', 'Trailblazer']:
        role_staff = df[df['rolename'] == role]
        for _, staff in role_staff.iterrows():
            subs = df['superiorcode'] == staff['customercode']
            subordinate_sales = df.loc[subs, 'sales'].sum()
            subordinate_override = df.loc[subs, 'overridesales'].sum()
            total_override = subordinate_sales + subordinate_override
            df.loc[df['customercode'] == staff['customercode'], 'overridesales'] = total_override
    return df

def compute_commissions(df):
    df = calculate_OverrideSales(df)
    df['commissionrate']     = df['rolename'].map(lambda r: network[r]['comm_rate'])
    df['overriderate']     = df['rolename'].map(lambda r: network[r]['override_rate'])
    df['personalcomm'] = df['sales'] * df['commissionrate']
    df['overridecomm'] = df['overridesales'] * df['overriderate']
    return df 