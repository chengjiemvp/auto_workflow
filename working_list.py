import pandas as pd

def get_list():
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
        new_df['Destination'].notna() &
        new_df['Vessel'].notna() &
        new_df['Voyage'].notna() &
        new_df['Remarks'].notna() &
        new_df['Description'].notna() &
        new_df['Marks'].notna()
        ]

    return working_lists

# working_list = get_list()
# for index, row in working_list.iterrows():
#     print(type(row))
#     print(row['ETA'].strftime(f"%m-%d-%Y"))
