network = {
    'Catalyst':    {'comm_rate': .35, 'override_rate': 0,   'level': 1},
    'Visionary':   {'comm_rate': .4,  'override_rate': .05,'level': 2},
    'Trailblazer': {'comm_rate': .4,  'override_rate': .05,'level': 3},
    'Agent':       {'comm_rate': .50, 'override_rate': 0,   'level': 4},
    'Agent 1':     {'comm_rate': .45, 'override_rate': 0,   'level': 5},
    'Agent 2':     {'comm_rate': .40, 'override_rate': 0,   'level': 6},
    'Agent 3':     {'comm_rate': .35, 'override_rate': 0,   'level': 7},
    'Agent 4':     {'comm_rate': .30, 'override_rate': 0,   'level': 8},
    'Agent 5':     {'comm_rate': .25, 'override_rate': 0,   'level': 9},
}

def calculate_OverrideSales(df):
    df['overridesales'] = 0
    for role in ['Catalyst', 'Visionary', 'Trailblazer']:
        role_staff = df[df['rolename'] == role]
        for _, staff in role_staff.iterrows():
            subs = df['superiorcode'] == staff['customercode']
            subordinate_sales = df.loc[subs, 'revenue'].sum()
            subordinate_override = df.loc[subs, 'overridesales'].sum()
            total_override = subordinate_sales + subordinate_override
            df.loc[df['customercode'] == staff['customercode'], 'overridesales'] = total_override
    return df

def compute_commissions(df):
    df = calculate_OverrideSales(df)
    df['commissionrate']     = df['rolename'].map(lambda r: network[r]['comm_rate'])
    df['overriderate']     = df['rolename'].map(lambda r: network[r]['override_rate'])
    df['personalcomm'] = df['totalprice'] * df['commissionrate'] 
    df['overridecomm'] = df['overridesales'] * df['overriderate']
    return df 

def calculate_quarterly_bonus(df):
    """
    Adds 'bonus_percentage' and 'bonus_value' columns to the input DataFrame
    based on the sales tiers defined in a network dictionary.
    The output format matches the commission output: all original columns, with bonus columns appended at the end.
    """
    network = [
        {'lower': 45_000_000, 'upper': 100_000_000, 'percent': 0.02},
        {'lower': 100_000_000, 'upper': 250_000_000, 'percent': 0.025},
        {'lower': 250_000_000, 'upper': 450_000_000, 'percent': 0.03},
        {'lower': 450_000_000, 'upper': 800_000_000, 'percent': 0.035},
        {'lower': 800_000_000, 'upper': 1_500_000_000, 'percent': 0.04},
        {'lower': 1_500_000_000, 'upper': 3_000_000_000, 'percent': 0.045},
        {'lower': 3_000_000_000, 'upper': float('inf'), 'percent': 0.05},
    ]
    bonus_percentages = []
    bonus_values = []
    for _, row in df.iterrows():
        sales = row['revenue']
        percent = 0.0
        for tier in network:
            if tier['lower'] <= sales < tier['upper']:
                percent = tier['percent']
                break
        bonus_percentages.append(percent)
        bonus_values.append(sales * percent)
    df['bonus_percentage'] = bonus_percentages
    df['bonus_value'] = bonus_values
    # Ensure bonus columns are at the end
    cols = [col for col in df.columns if col not in ['bonus_percentage', 'bonus_value']] + ['bonus_percentage', 'bonus_value']
    df = df[cols]
    return df 