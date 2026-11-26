"""Utilidades independientes del dominio; las reglas de negocio viven en cada caso."""
from pathlib import Path

import pandas as pd


def read_table(path, **kwargs):
    path = Path(path)
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path, **kwargs)
    if path.suffix.lower() == '.xlsx':
        return pd.read_excel(path, **kwargs)
    raise ValueError(f'Formato no soportado: {path.suffix}')

def profile(df):
    return pd.DataFrame({'column': df.columns, 'dtype': df.dtypes.astype(str).values,
                         'nulls': df.isna().sum().values, 'unique': df.nunique().values,
                         'rows': len(df), 'exact_duplicates': int(df.duplicated().sum())})

def numeric(series):
    return pd.to_numeric(series, errors='coerce')

def audited_join(left, right, key, validate='many_to_one'):
    joined = left.merge(right, on=key, how='left', validate=validate, indicator=True)
    audit = joined['_merge'].value_counts().rename_axis('status').reset_index(name='rows')
    return joined.drop(columns='_merge'), audit

def export_tables(path, tables):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
        for name, df in tables.items():
            df.to_excel(writer, sheet_name=name, index=False)
            writer.sheets[name].freeze_panes(1, 0)
