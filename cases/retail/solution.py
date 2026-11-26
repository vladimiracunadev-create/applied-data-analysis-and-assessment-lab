from pathlib import Path

from lab.core import export_tables, profile, read_table

HERE = Path(__file__).resolve().parent

def analyze(raw):
    df = raw.drop_duplicates().copy()
    df = df[df.quantity.gt(0) & df.price.ge(0) & df.cost.ge(0) & df.status.isin(['SALE','RETURN'])].copy()
    df['units'] = df.quantity.where(df.status.eq('SALE'), -df.quantity)
    df['net_sales'] = df.units * df.price
    df['margin'] = df.units * (df.price-df.cost)
    result = df.groupby('product')[['units','net_sales','margin']].sum().reset_index()
    return {'quality': profile(raw), 'metrics': result}

if __name__ == '__main__':
    export_tables(HERE/'reference.xlsx', analyze(read_table(HERE/'input.csv')))
