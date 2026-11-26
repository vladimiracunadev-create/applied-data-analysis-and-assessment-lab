import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pandas as pd

from cases.education.solution import analyze as education
from cases.retail.solution import analyze as retail
from lab.core import audited_join, profile


def test_retail():
    df=pd.DataFrame({'id':[1,2,3], 'product':['A']*3,'quantity':[2,1,-1],'price':[100]*3,'cost':[40]*3,'status':['SALE','RETURN','SALE']})
    assert retail(df)['metrics'].iloc[0].net_sales==100

def test_education():
    df=pd.DataFrame({'id':[1,2], 'school':['A','A'],'attended':[1,9],'scheduled':[2,10]})
    assert abs(education(df)['metrics'].iloc[0].weighted_pct-100*10/12)<1e-9

def test_join():
    result,audit=audited_join(pd.DataFrame({'id':[1,2]}),pd.DataFrame({'id':[1],'name':['A']}),'id')
    assert len(result)==2 and result.name.isna().sum()==1
    assert profile(result).set_index('column').loc['name','nulls']==1
