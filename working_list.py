import pandas as pd

def working_list():
    df = pd.read_excel('./TEST.xlsx', sheet_name='WorkingShips')
    new_df = df[df['OI'].isna() & df['Date'].notna()]

    working_lists = new_df[
        new_df['Type'].notna() &
        new_df['Express'].notna() &
        new_df['MBL'].notna() &
        new_df['HBL'].notna() &
        new_df['ContainerNu'].notna() &
        new_df['Fee'].notna() &
        new_df['ETA'].notna() &
        new_df['POL'].notna() &
        new_df['POD'].notna() &
        new_df['FinalDes'].notna() &
        new_df['FclTrk'].notna() &
        new_df['DODate'].notna() &
        new_df['Terminal'].notna() &
        new_df['TrainSta'].notna() &
        new_df['Destination'].notna()
        ]

    for key,value in working_lists.iterrows():
        print(f"{key}:========================================\n{value}")
        
    return working_lists
