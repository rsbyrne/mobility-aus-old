import string
import os
import re

import numpy as np
import pandas as pd
df = pd.DataFrame

import os
dirPath = os.path.abspath(os.path.dirname(__file__))
dataDir = os.path.join(dirPath, 'products')

lookupName = 'abs_lookup.csv'
lookupPath = os.path.join(dataDir, lookupName)
assert os.path.exists(lookupPath)
lookupFrm = pd.read_csv(lookupPath)
lookupFrm['code'] = lookupFrm['code'].astype(str)

def remove_brackets(x):
    return re.sub("[\(\[].*?[\)\]]", "", x).strip()

def events_annotate(ax, series, region, lims = (None, None), points = None):
    eventsFrm = pd.read_csv(os.path.join(dataDir, f'events_{region}.csv'))
    eventsFrm['date'] = eventsFrm['date'].astype(np.datetime64)
    if not lims[0] is None:
        eventsFrm = eventsFrm.loc[eventsFrm['date'] >= lims[0]]
    if not lims[1] is None:
        eventsFrm = eventsFrm.loc[eventsFrm['date'] <= lims[1]]
    events = list(zip(eventsFrm['date'], eventsFrm['event']))
    letterOptions = [l for l in string.ascii_lowercase]
    for l in string.ascii_lowercase:
        for sl in string.ascii_lowercase:
            letterOptions.append(l + sl)
    keys = []
    for i, (date, label) in enumerate(events):
        letter = letterOptions[i]
        keys.append((letter, label))
        xtarget = date
        if xtarget in series.index:
            ytarget = series.loc[xtarget]
        else:
            diffSeries = pd.Series(abs(series.index - xtarget), series.index)
            nearest = diffSeries.loc[diffSeries == diffSeries.min()].index
            ytarget = series.loc[nearest].iloc[0]
        ax.annotate(xtarget, ytarget, letter, points = points)
    marktable = '| Key | Event | \n | --- | --- | \n'
    for letter, label in keys:
        marktable += f'| {letter} | {label} | \n'
    return marktable

# def unit_axis(data):
#     return window.data.Data(data, lims = (None, 1.), capped = (False, True))

def average(frm, key):
    func = lambda d: (d[key] * d['dateweight']).sum()
    return frm.groupby('date').apply(func)
def pop_average(frm, key):
    global lookupFrm
    allPop = lookupFrm.groupby('type')['pop'].sum()['lga']
    func = lambda d: (d[key] * d['pop'] / allPop).sum()
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

def make_melvic_dataFrm():

    melFrm = make_dataFrm(region = 'mel', dropna = False)
    melFrm = melFrm.loc[melFrm['name'] != 'Greater Geelong']
    vicFrm = make_dataFrm(region = 'vic', dropna = True)

    indices = list(set.intersection(set(melFrm.index), set(vicFrm.index)))
    melFrm = melFrm.loc[indices].sort_index()
    vicFrm = vicFrm.loc[indices].sort_index()

    reweight(melFrm)
    reweight(vicFrm)

    frm = melFrm.copy()
    frm['stay'] = melFrm['stay'] * (1. + vicFrm['stay']) / 2.
    frm['adjstay'] = melFrm['adjstay'] * (1. + vicFrm['adjstay']) / 2.
    frm['km'] = (melFrm['km'] + vicFrm['km']) / 2
#     frm['stayscore'] = (melFrm['stayscore'] + vicFrm['stayscore']) / 2.
    frm['stayscore'] = get_stayscore(frm)

    return frm

def make_dataFrm(region, dropna = False):
    
    dataName = f'mob_lga_{region}.csv'
    dataPath = os.path.join(dataDir, dataName)
    assert os.path.exists(dataPath)

    global lookupFrm

    dataFrm = pd.read_csv(dataPath)
    dataFrm['date'] = dataFrm['date'].astype(np.datetime64) #pd.to_datetime(dataFrm['date'])
    dataFrm['code'] = dataFrm['code'].astype(int).astype(str)

    dataFrm = dataFrm.reset_index()
    filt = dataFrm.groupby('code')['stay'].apply(lambda s: s.max() != s.min())
    dataFrm = dataFrm.set_index('code').loc[filt.index]
    dataFrm = dataFrm.reset_index().set_index(['date', 'code'])

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
    dataFrm['km'] = dataFrm['km'].fillna(dataFrm['km'].min() / 2)

    dataFrm['adjstay'] = get_adjstay(dataFrm)
    dataFrm['stayscore'] = get_stayscore(dataFrm)

#     dataFrm = dataFrm.loc[dataFrm['date'] >= '2020-04-05']

    dataFrm = dataFrm.sort_index()

    reweight(dataFrm)

    return dataFrm

def get_adjstay(frm):
    from scipy.special import expit
    frm = frm.copy()
    tileArea = frm['km'].min() ** 2
    popPerTile = frm['pop'] * tileArea / frm['area']
    mob = (1. - frm['stay'])
    fbFrac = 1 / 10
    fbThresh = 10
    destTiles = frm['km'] ** 2 / tileArea
    detChance = expit((popPerTile * fbFrac / destTiles - fbThresh) / fbThresh)
    trav = (mob / detChance).apply(lambda x: min(x, 1.))
    adjStay = 1. - trav
    return adjStay

def get_stayscore(frm):
    frm = frm.copy()
    frm = frm.reset_index()
    frm['rawscore'] = frm['adjstay'] #* frm['km']
    groups = frm.groupby(['code', 'day'])['rawscore']
    bests = groups.apply(lambda s: s.nlargest(4).mean())
    worsts = groups.apply(lambda s: s.nsmallest(4).mean())
    frm = frm.set_index(['code', 'day', 'date']).sort_index()
    frm = frm.loc[bests != worsts]
    scores = ((frm['rawscore'] - worsts) / (bests - worsts))
    # scores = scores.apply(lambda s: max(0, min(1, s)))
    scores = scores.sort_index()
    frm['stayscore'] = scores
    frm = frm.reset_index().set_index(['date', 'code'])
    return frm['stayscore']

def get_stayscore_series(series):
    days = [int(d.strftime('%w')) for d in series.index.tolist()]
    codes = ['ignore' for d in days]
    frm = df({
        'adjstay': series.values,
        'day': days,
        'code': codes,
        'date': series.index
        }).set_index(['date', 'code'])
    scores = get_stayscore(frm).xs('ignore', level = 'code').sort_index()
    return scores