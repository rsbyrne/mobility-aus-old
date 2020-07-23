import string
import os
import re

import numpy as np
import pandas as pd

import window
from window.data import Data

dirPath = os.path.abspath(os.path.dirname(__file__))
dataDir = os.path.join(dirPath, 'products')

def remove_brackets(x):
    return re.sub("[\(\[].*?[\)\]]", "", x).strip()

def events_annotate(ax, series, region):
    eventsFrm = pd.read_csv(os.path.join(dataDir, f'events_{region}.csv'))
    events = list(zip(eventsFrm['date'], eventsFrm['event']))
    letterOptions = [l for l in string.ascii_lowercase]
    for l in string.ascii_lowercase:
        for sl in string.ascii_lowercase:
            letterOptions.append(l + sl)
    keys = []
    for i, (date, label) in enumerate(events):
        letter = letterOptions[i]
        keys.append((letter, label))
        xtarget = np.datetime64(date)
        if xtarget < series.index.min():
            ytarget = series.loc[series.index.min()]
        elif xtarget > series.index.max():
            ytarget = series.loc[series.index.max()]
        else:
            ytarget = series.loc[xtarget]
        ax.annotate(xtarget, ytarget, letter, points = 10)
    marktable = '| Key | Event | \n | --- | --- | \n'
    for letter, label in keys:
        marktable += f'| {letter} | {label} | \n'
    return marktable

def unit_axis(data):
    return window.data.Data(data, lims = (None, 1.), capped = (False, True))

def average(frm, key):
    func = lambda d: (d[key] * d['dateweight']).sum()
    return frm.groupby('date').apply(func)

def get_owid_cases(region):
    cases = pd.read_csv('https://covid.ourworldindata.org/data/owid-covid-data.csv')
    cases = cases.loc[cases['location'] == region]
    cases = cases[['date', 'new_cases', 'total_cases']]
    cases['date'] = cases['date'].astype(np.datetime64)
    cases = cases.set_index('date')
    cases = cases.loc[cases.index >= dataFrm['date'].min()]
    cases = cases.loc[cases.index <= dataFrm['date'].max()]
    return cases

def reweight(frm):
    frm['weight'] /= frm['weight'].sum()
    frm['dateweight'] = frm.groupby(frm.index.get_level_values('date'))['weight'].apply(lambda s: s / s.sum())
    frm['codeweight'] = frm.groupby(frm.index.get_level_values('code'))['weight'].apply(lambda s: s / s.sum())

def make_casesFrm(region = 'vic'):
    if not region == 'vic':
        raise Exception
    cases = pd.read_json("https://covidlive.com.au/covid-live-loc.json")
    cases = cases.rename(
        dict(
            REPORT_DATE = 'date',
            LOCALITY_NAME = 'name',
            CASE_CNT = 'cases',
            ACTIVE_CASE_CNT = 'active',
            ),
        axis = 1
        )
    cases = cases.drop(['ID', 'LOCALITY_TYPE', 'CODE'], axis = 1)
    cases['date'] = cases['date'].astype(np.datetime64)
    cases = cases.set_index(['date', 'name'])
    cases = cases.sort_index()
    return cases

def make_dataFrm(region, dropna = False):
    
    dataName = f'mob_lga_{region}.csv'
    dataPath = os.path.join(dataDir, dataName)
    assert os.path.exists(dataPath)

    lookupName = 'abs_lookup.csv'
    lookupPath = os.path.join(dataDir, lookupName)
    assert os.path.exists(lookupPath)

    dataFrm = pd.read_csv(dataPath)
    dataFrm['date'] = dataFrm['date'].astype(np.datetime64) #pd.to_datetime(dataFrm['date'])
    dataFrm['code'] = dataFrm['code'].astype(int).astype(str)

    lookupFrm = pd.read_csv(lookupPath)
    lookupFrm['code'] = lookupFrm['code'].astype(str)

    dataFrm = dataFrm.reset_index()
    codeFrm = lookupFrm.set_index('code').loc[dataFrm['code']][['name', 'area', 'pop']]
    dataFrm = dataFrm.set_index('code')
    dataFrm[['name', 'area', 'pop']] = codeFrm
    dataFrm['name'] = dataFrm['name'].apply(remove_brackets)
    dataFrm['density'] = dataFrm['pop'] / dataFrm['area']
    dataFrm['tiles'] = dataFrm['area'] / dataFrm['km'].min() ** 2
    dataFrm = dataFrm.reset_index()
    dataFrm = dataFrm.drop('index', axis = 1)
    dataFrm['day'] = [int(d.strftime('%w')) for d in dataFrm['date'].tolist()]

    if dropna:
        dataFrm = dataFrm.dropna()
        todrop = []
        for code in set(dataFrm['code']):
            codeFrm = dataFrm.loc[dataFrm['code'] == code]
            if not len(codeFrm) == len(set(dataFrm['date'])):
                todrop.append(code)
        for code in todrop:
            dataFrm = dataFrm.loc[dataFrm['code'] != code]

    dataFrm = dataFrm.set_index(['date', 'code']).sort_index()
    reweight(dataFrm)

#     dataFrm = dataFrm.loc[dataFrm['date'] >= '2020-04-05']

    dataFrm = dataFrm.reset_index()
    filt = dataFrm.groupby('code')['stay'].apply(lambda s: s.max() != s.min())
    dataFrm = dataFrm.set_index('code').loc[filt.index].reset_index()

    dataFrm = dataFrm.set_index(['date', 'code'])
    dataFrm['stayscore'] = get_stayscore(dataFrm)

    dataFrm = dataFrm.sort_index()

    return dataFrm

def get_stayscore(frm):
    frm = frm.reset_index()
    groups = frm.groupby(['code', 'day'])['stay']
    bests = groups.apply(lambda s: s.nlargest(3).mean())
    worsts = groups.apply(lambda s: s.nsmallest(3).mean())
    frm = frm.set_index(['code', 'day', 'date']).sort_index()
    frm = frm.loc[bests != worsts]
    scores = ((frm['stay'] - worsts) / (bests - worsts))
    # scores = scores.apply(lambda s: max(0, min(1, s)))
    scores = scores.sort_index()
    frm['stayscore'] = scores
    frm = frm.reset_index().set_index(['date', 'code'])
    return frm['stayscore']