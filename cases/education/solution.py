from pathlib import Path

from lab.core import export_tables, profile, read_table

HERE = Path(__file__).resolve().parent

def analyze(raw):
    df = raw.drop_duplicates().copy()
    df = df[df.scheduled.gt(0) & df.attended.between(0,df.scheduled)].copy()
    df['rate'] = 100*df.attended/df.scheduled
    result = df.groupby('school').agg(attended=('attended','sum'),scheduled=('scheduled','sum'),simple_pct=('rate','mean')).reset_index()
    result['weighted_pct'] = 100*result.attended/result.scheduled
    return {'quality': profile(raw), 'metrics': result}

if __name__ == '__main__':
    export_tables(HERE/'reference.xlsx', analyze(read_table(HERE/'input.csv')))
