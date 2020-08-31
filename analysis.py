import string
import os
import re

import numpy as np
import pandas as pd
from scipy.special import expit

import load

dirPath = os.path.abspath(os.path.dirname(__file__))
dataDir = os.path.join(dirPath, 'products')

def events_annotate(ax, series, region, lims = (None, None), points = None, returnTable = False):

    # Get events data:
    eventsFrm = pd.read_csv(os.path.join(dataDir, f'events_{region}.csv'))
    eventsFrm['date'] = eventsFrm['date'].astype('datetime64[ns]')

    # Trim by provided lims:
    if not lims[0] is None:
        eventsFrm = eventsFrm.loc[eventsFrm['date'] >= lims[0]]
    if not lims[1] is None:
        eventsFrm = eventsFrm.loc[eventsFrm['date'] <= lims[1]]

    # Make events/letters lookup table:
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

    # Return desired format:
    if returnTable:
        marktable = '| Key | Event | \n | --- | --- | \n'
        for letter, label in keys:
            marktable += f'| {letter} | {label} | \n'
        return marktable
    else:
        return keys

def make_lookupFrm():
    # Load and correct ABS lookup frame:
    global dataDir
    lookupName = 'abs_lookup.csv'
    lookupPath = os.path.join(dataDir, lookupName)
    assert os.path.exists(lookupPath)
    lookupFrm = pd.read_csv(lookupPath)
    lookupFrm['code'] = lookupFrm['code'].astype(str)
    return lookupFrm
def make_sub_lookupFrm(state = None, aggType = None):
    lookup = make_lookupFrm()
    lookup['name'] = lookup['name'].apply(remove_brackets)
    if not state is None:
        lookup = lookup.loc[lookup['state'] == state]
    if not aggType is None:
        lookup = lookup.loc[lookup['type'] == aggType]
    lookup = lookup[['name', 'area', 'pop']]
    lookup = lookup.set_index('name')
    return lookup

def make_casesFrm_monash(region = 'vic'):

    if not region in {'vic', 'mel'}:
        raise Exception

    # From Monash
    # Load data:
    cases = pd.read_csv('https://homepages.inf.ed.ac.uk/ngoddard/covid19/vicdata/lgadata.csv')
    pop = dict(cases.loc[cases['Date'] == 'Population'].iloc[0].drop('Date'))
    cases = cases.drop([0, 1, 2])
    cases['Date'] = cases['Date'].astype('datetime64[ns]')
    cases = cases.rename(mapper = dict(Date = 'date'), axis = 1)

    # Restructure array:
    cases = cases.melt('date', var_name = 'name', value_name = 'cumulative')
    cases = cases.set_index(['date', 'name'])
    cases = cases.loc[~cases.index.duplicated()]
    cases = cases.fillna(0).astype(int)
    cases = cases.sort_index()

    # Correct population figures:
    lookup = make_sub_lookupFrm(region, 'lga')
    popDict = dict(zip(lookup.index, lookup['pop']))
    cases['pop'] = [popDict[n] for n in cases.index.get_level_values('name')]

    # Derive 'new cases' metric:
    cases['new'] = cases['cumulative'].groupby(level = 'name') \
        .diff().dropna().astype(int)
    cases = cases.dropna()
    cases['new'] = cases['new'] / cases['pop'] * 10000
    cases['new_rolling'] = cases['new'].groupby(level = 'name', group_keys = False) \
        .rolling(7).mean().sort_index()

    # Add averages:
    serieses = dict()
    weightKey = 'pop'
    level = 'date'
    for key in [key for key in cases if not key == weightKey]:
        fn = lambda f: np.average(f[key], weights = f[weightKey])
        series = cases[[key, weightKey]].groupby(level = level).apply(fn)
        serieses[key] = series
    avFrm = pd.DataFrame(serieses)
    avFrm['name'] = 'average'
    avFrm = avFrm.reset_index().set_index(['date', 'name'])
    cases = cases.drop(weightKey, axis = 1)
    cases = cases.append(avFrm)
    cases = cases.dropna().sort_index()

    # Return:
    return cases

def make_casesFrm_covidlive(region = 'vic'):

    region = 'vic'

    if not region in {'vic', 'mel'}:
        raise Exception

    lookup = make_sub_lookupFrm(region, 'lga') #pd.read_csv('../products/abs_lookup.csv')
    popDict = dict(zip(lookup.index, lookup['pop']))

    renameDict = dict(
        REPORT_DATE = 'date',
        LOCALITY_NAME = 'name',
        CASE_CNT = 'cumulative'
        )

    cases = pd.read_json("https://covidlive.com.au/covid-live-loc.json")
    cases = cases.rename(mapper = renameDict, axis = 1)
    cases = cases[sorted(renameDict.values())]
    cases['date'] = cases['date'].astype('datetime64[ns]')
    cases = cases.set_index(['date', 'name'])
    cases = cases.drop([k for k in cases.index.levels[1] if not k in popDict], level = 'name')
    cases['pop'] = [popDict[n] for n in cases.index.get_level_values('name')]

    # Derive 'new cases' metric:
    cases['new'] = cases['cumulative'].groupby(level = 'name') \
        .diff().dropna().astype(int)
    cases['new'] = cases['new'] / cases['pop'] * 10000
    cases['new_rolling'] = cases['new'].groupby(level = 'name', group_keys = False) \
        .rolling(7).mean().sort_index()

    # Add averages:
    serieses = dict()
    weightKey = 'pop'
    level = 'date'
    for key in [key for key in cases if not key == weightKey]:
        fn = lambda f: np.average(f[key], weights = f[weightKey])
        series = cases[[key, weightKey]].groupby(level = level).apply(fn)
        serieses[key] = series
    avFrm = pd.DataFrame(serieses)
    avFrm['name'] = 'average'
    avFrm = avFrm.reset_index().set_index(['date', 'name'])
    cases = cases.drop(weightKey, axis = 1)
    cases = cases.append(avFrm)
    cases = cases.dropna().sort_index()

    # Return:
    return cases

def make_casesFrm(region = 'vic'):
    monashCases = make_casesFrm_monash(region)
    covidliveCases = make_casesFrm_covidlive(region)
    trimmedMonashCases = monashCases.loc[
        monashCases.index.get_level_values('date') \
        < covidliveCases.index.get_level_values('date').min()
        ]
    cases = pd.concat([trimmedMonashCases, covidliveCases]).sort_index()
    return cases

def remove_brackets(x):
    # Remove brackets from ABS council names:
    return re.sub("[\(\[].*?[\)\]]", "", x).strip()

def calculate_day_scores(series, level = 'date', n = 4):
    # Takes a series indexed by date
    # and returns normalised values grouped by date
    index = series.index.get_level_values(level)
    series = pd.DataFrame(data = dict(
        val = series.values,
        date = index,
        day = [int(d.strftime('%w')) for d in index.tolist()]
        )).set_index([level, 'day'])['val']
    groups = series.groupby(level = 'day')
    highs = groups.apply(lambda s: s.nlargest(n).mean())
    lows = groups.apply(lambda s: s.nsmallest(n).mean())
    series = (series - lows) / (highs - lows)
    series = pd.Series(series.values, index)
    return series

def calculate_averages(frm, level = 'date', weightKey = 'pop'):
    # Get a frame that contains averages by some chosen level
    serieses = dict()
    level = 'date'
    weightKey = 'pop'
    for key in [col for col in frm.columns if not col == weightKey]:
        fn = lambda f: np.average(f[key], weights = f[weightKey])
        series = frm[[key, weightKey]].groupby(level = level).apply(fn)
        serieses[key] = series
    return pd.DataFrame(serieses)

def make_dataFrm(region):

    global dataDir

    # Load raw data
    dataName = f'mob_lga_{region}.csv'
    rawPath = os.path.join(dataDir, dataName)
    frm = pd.read_csv(rawPath)
    cases = make_casesFrm()

    # Correct data types from csv
    frm['code'] = frm['code'].astype(int).astype(str)
    frm['date'] = frm['date'].astype('datetime64[ns]')

    # Filter out data with no variation on a key metric
    filt = frm.groupby('code')['stay'].apply(lambda s: s.max() != s.min())
    frm = frm.set_index('code').loc[filt.index].reset_index()

    # Add council information from lookupFrm
    lookupFrm = make_lookupFrm()
    codeFrm = lookupFrm.set_index('code').loc[frm['code']][['name', 'area', 'pop']]
    frm = frm.set_index('code')
    frm[['name', 'area', 'pop']] = codeFrm
    frm = frm.reset_index()

    # Trim brackets from council names
    frm['name'] = frm['name'].apply(remove_brackets)

    # Add a nominal distance travelled when below detection threshold
    frm['km'] = frm['km'].fillna(frm['km'].min() / 2)

    # Adjust 'stay' metric to account for detection cutoffs
    tileArea = frm['km'].min() ** 2
    popPerTile = frm['pop'] * tileArea / frm['area']
    mob = (1. - frm['stay'])
    fbFrac = 1 / 10
    fbThresh = 10
    destTiles = frm['km'] ** 2 / tileArea
    detChance = expit((popPerTile * fbFrac / destTiles - fbThresh) / fbThresh)
    trav = (mob / detChance).apply(lambda x: min(x, 1.))
    adjStay = 1. - trav
    frm['stay'] = adjStay

    # Drop redundant columns
    frm = frm.drop(['area', 'code', 'weight'], axis = 1)

    # Reindex to final form
    frm = frm.set_index(['date', 'name'])

    # Get scores
    scores = frm.groupby(level = 'name')['stay'].apply(calculate_day_scores)
    scores = scores.reorder_levels([1, 0]).sort_index()
    frm['score'] = scores

    # Add cases data
    cases = cases.reindex(frm.index).loc[frm.index]
    frm[cases.columns] = cases

    # Get averages
    averages = calculate_averages(frm)
    averages['name'] = 'average'
    averages = averages.reset_index().set_index(['date', 'name']).sort_index()
    frm = frm.append(averages).sort_index()

    # Final sort
    frm = frm.sort_index()

    # Return:
    return frm

def make_geometry(indices, region = 'vic'):
    statesLookup = dict(
        vic = 'Victoria',
        mel = 'Victoria',
        nsw = 'New South Wales',
        syd = 'Sydney',
        )
    # Make a geometry frame from ABS data:
    lgas = load.load_lgas()
    lgas = lgas.loc[lgas['STE_NAME16'] == statesLookup[region]]
    lgas['name'] = lgas['name'].apply(remove_brackets)
    lgas = lgas.set_index('name')
    councils = [c for c in indices if c in lgas.index]
    geometry = lgas['geometry'].loc[councils]
    return geometry

def make_melvicFrm():

    # Get component frames
    melFrm = make_dataFrm('mel')
    melFrm = melFrm.drop('Greater Geelong', level = 'name')
    melFrm = melFrm.drop('Queenscliffe', level = 'name')
    vicFrm = make_dataFrm('vic')
    indices = list(set.intersection(set(melFrm.index), set(vicFrm.index)))
    melFrm = melFrm.loc[indices].sort_index()
    vicFrm = vicFrm.loc[indices].sort_index()

    # Merge frames
    frm = melFrm.copy()
    frm['stay'] = melFrm['stay'] * (1. + vicFrm['stay']) / 2.
    frm['km'] = (melFrm['km'] + vicFrm['km']) / 2

    # Calculate new scores
    scores = frm.groupby(level = 'name')['stay'].apply(calculate_day_scores)
    scores = scores.reorder_levels([1, 0]).sort_index()
    frm['score'] = scores

    # Calculate new averages
    frm = frm.drop('average', level = 'name')
    averages = calculate_averages(frm)
    averages['name'] = 'average'
    averages = averages.reset_index().set_index(['date', 'name']).sort_index()
    frm = frm.append(averages).sort_index()

    # Calculate new average score
    avScores = calculate_day_scores(frm['score'].xs('average', level = 'name'))
    frm.loc[(slice(None), 'average'), 'score'] = avScores.to_list()

    # Drop redundant columns
    frm = frm.drop('pop', axis = 1)

    # Return
    return frm