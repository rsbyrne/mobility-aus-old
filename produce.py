import numpy as np
import math
import os

import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame
import shapely
import mercantile

import load
import utils
import processing
import aggregate

repoPath = os.path.abspath(os.path.dirname(__file__))

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def get_abs_lookup(sources, refresh = False):
    filename = 'abs_lookup.csv'
    filePath = os.path.join(repoPath, 'products', filename)
    if os.path.isfile(filePath) and not refresh:
        out = pd.read_csv(filePath)
        out = out.set_index('code')
        if not all([source in set(out['type']) for source in sources]):
            return get_abs_lookup(sources, refresh = True)
        return out
    else:
        out = make_abs_lookup(sources)
        out.to_csv(filePath)
        return out
def make_abs_lookup(sources):
    frms = []
    for source in sources:
        frm = load.load_generic(source)
        frm = frm[['name']]
        frm['type'] = source
        frm.index.name = 'code'
        frms.append(frm)
    frm = pd.concat(frms)
    frm = frm.sort_index()
    return frm

def make_mob_plots(frm, region, aggType = 'lga'):

    frm = frm.reset_index()
    func = lambda x: (x['stay'] * x['weight']).sum()
    dateAvs = frm.groupby('date')[['weight', 'stay']].apply(func)
    regionAvs = frm.groupby('code')[['weight', 'stay']].apply(func)

    fig, ax = plt.subplots(2)
    dateAvs.plot(
        title = 'Net stay-at-home ratio per day',
        ax = ax[0]
        )
    adjRegionAvs = regionAvs.sort_values().apply(lambda x: x - np.median(regionAvs))
    adjRegionAvs.plot.bar(
        title = 'All-time stay-at-home ratio per region relative to median',
        ax = ax[1]
        )
    fig.tight_layout(pad = 0.5)
    fig.set_size_inches(6, 7)

    filename = '_'.join(['mob', aggType, region]) + '.png'
    filePath = os.path.join(repoPath, 'products', filename)
    fig.savefig(filePath)

def get_mob_date(region, aggType = 'lga', refresh = False, get = False, override = False):
    filename = '_'.join(['mob', aggType, region]) + '.csv'
    filePath = os.path.join(repoPath, 'products', filename)
    if os.path.isfile(filePath) and not refresh:
        out = pd.read_csv(filePath)
        out['date'] = pd.to_datetime(out['date'])
        out = out.set_index(['date', 'code'])
        return out
    else:
        out = make_mob_date(region, aggType, get = get, override = override)
        out.to_csv(filePath)
        return out
def make_mob_date(region, aggType = 'lga', get = False, override = False):

    mob = load.load_fb_tiles(region, 'mob', get = get, override = override)

    agg = aggregate.aggregate_mob_tiles_to_abs(mob, region, aggType)
    agg = aggregate.aggregate_by_date(agg)

    frm = agg.copy()
    frm = frm.reset_index()
    frm['n'] *= frm['weight']
    frm['km'] *= frm['n']
    frm.loc[frm['km'] == 0., 'stay'] = frm['n']

    trav = frm.loc[frm['start'] != frm['stop']].loc[frm['km'] > 0.].copy()
    dateN = trav.groupby('date')['n'].aggregate(sum)
    stopCounts = trav.groupby(['date', 'stop'])['n'].aggregate(sum)
    visit = stopCounts / dateN
    visit.index.names = ['date', 'code']

    frm = frm.rename(dict(start = 'code'), axis = 1)
    frm = frm.set_index(['date', 'code'])
    frm = frm.drop('stop', axis = 1)
    procFrm = frm

    frm = procFrm.copy()
    frm = aggregate.aggregate_identicals(
        frm,
        n = sum,
        km = sum,
        stay = sum
        )
    frm['stay'] /= frm['n']
    frm['km'] = frm['km'] / (frm['n'] * (1. - frm['stay']))
    frm['weight'] = frm['n'] / frm.reset_index().groupby('date')['n'].aggregate(sum)
    frm['visit'] = visit
    frm['visit'] = frm['visit'].fillna(0.)
    frm = frm.drop('n', axis = 1)
    out = frm

    return out

def make_mob_dateMap(raw, region, aggType = 'lga'):

    frm = raw.copy()
    frms = []
    for key in [key for key in raw.columns if not key == 'geometry']:
        subFrm = utils.pivot(frm, 'code', 'date', key)[key]
        subFrm.columns = [
            str(round(int(n.to_numpy()) / 1e6)) if type(n) is pd.Timestamp else n
                for n in subFrm.columns
            ]
        subFrm.columns = ['_'.join([key, n]) for n in subFrm.columns]
        frms.append(subFrm)
    concatFrm = pd.concat(frms, axis = 1)

    frm = concatFrm.copy()
    indexNames = frm.index.names
    frm = frm.reset_index()
    aggRegions = load.load_generic(aggType)
    frm['geometry'] = frm['code'].apply(lambda x: aggRegions.loc[x]['geometry'])
    frm = frm.set_index(indexNames)
    frm = gdf(frm)
    frm['name'] = aggRegions.loc[frm.index]['name']
    frm['area'] = aggRegions.loc[frm.index]['area']

    scale = np.sqrt(np.median(frm['geometry'].area))
    scalingCoeff = len(frm) ** 2. * 1e-5
    frm['geometry'] = frm['geometry'].simplify(scale * scalingCoeff)
    frm['geometry'] = frm['geometry'].buffer(scale * 0.1 * scalingCoeff)

    mapName = '_'.join(['mob', aggType, region])
    titlesDict = {
        'aus': 'Australia',
        'vic': 'Victoria',
        'mel': 'Melbourne',
        'nsw': 'New South Wales',
        'syd': 'Sydney',
        'qld': 'Queensland',
        'nt': 'Northern Territory',
        'dar': 'Darwin',
        'act': 'Australian Capital Territory',
        'sa': 'South Australia',
        'ade': 'Adelaide',
        'wa': 'Western Australia',
        'per': 'Perth',
        'tas': 'Tasmania',
        'hob': 'Hobart',
        }
    mapTitle = '{0} mobility chart'.format(titlesDict[region])

    make_dateMap(frm, mapName, mapTitle, size = 600, nonVisKeys = {'name', 'area'})

def make_dateMap(frm, name, title, size = 600, nonVisKeys = {}):

    minx = np.min(frm.bounds['minx'])
    maxx = np.max(frm.bounds['maxx'])
    miny = np.min(frm.bounds['miny'])
    maxy = np.max(frm.bounds['maxy'])
    aspect = (maxx - minx) / (maxy - miny)

    ts = sorted(set([n.split('_')[-1] for n in frm.columns]))
    ts = [n for n in ts if n.isnumeric()]
    assert len(ts)
    ns = sorted(set([n.split('_')[0] for n in frm.columns]))
    ns = [n for n in ns if not n in [*nonVisKeys, 'geometry']]
    assert len(ns)

    defaultCol = '_'.join([ns[0], ts[-1]])

    indexName = frm.index.name

    mins = {n: frm[['_'.join([n, t]) for t in ts]].min().min() for n in ns}
    maxs = {n: frm[['_'.join([n, t]) for t in ts]].max().max() for n in ns}

    from bokeh.models import GeoJSONDataSource
    geoJSON = frm.reset_index().to_json()
    source = GeoJSONDataSource(geojson = geoJSON)

    from bokeh.io import output_file
    outFilename = name + '.html'
    outPath = os.path.join(repoPath, 'products', outFilename)
    if os.path.isfile(outPath):
        os.remove(outPath)
    output_file(outPath)

    from bokeh.plotting import figure
    fig = figure(
        title = title,
        plot_height = size,
        plot_width = int(round(size * aspect)) + 50, 
        toolbar_location = 'right',
        tools = 'pan, zoom_in, zoom_out, wheel_zoom, reset',
        background_fill_color = "lightgrey"
        )

    fig.xgrid.grid_line_color = None
    fig.ygrid.grid_line_color = None

    from bokeh.palettes import Viridis256
    from bokeh.models import LinearColorMapper, ColorBar
    palette = Viridis256
    colourMapper = LinearColorMapper(
        palette = palette,
        low = mins[ns[0]],
        high = maxs[ns[0]],
        )
    colourBar = ColorBar(
        color_mapper = colourMapper, 
        label_standoff = 8,
        width = 30,
        height = int(round(fig.plot_height * 0.9)),
        border_line_color = None,
        location = (0, 0), 
        orientation = 'vertical',
        )
    fig.add_layout(colourBar, 'left')

    patches = fig.patches(
        'xs',
        'ys',
        source = source,
        fill_color = dict(
            field = defaultCol,
            transform = colourMapper,
            ),
        line_color = 'grey', 
        line_width = 0.25,
        fill_alpha = 1,
        name = defaultCol
        )

    from bokeh.models.widgets import DateSlider as Slider
    slider = Slider(
        title = 'Date',
        start = int(ts[0]),
        end = int(ts[-1]),
        step = int(8.64 * 1e7), # days
        value = int(ts[-1]),
        width = fig.plot_width - 70
        )

    from bokeh.models.widgets import Select
    select = Select(
        title = "Dataset",
        options = ns,
        value = defaultCol.split('_')[0],
        width = 60
        )

    from bokeh.models import CustomJS
    callback = CustomJS(
        args = dict(
            patches = patches,
            source = source,
            slider = slider,
    #         key = 'stay', # <--- TESTING
            select = select,
            colourMapper = colourMapper,
            mins = mins,
            maxs = maxs,
            ),
        code = """
            const newCol = select.value + '_' + slider.value
            patches.glyph.fill_color['field'] = newCol
            patches.name = newCol
            colourMapper.low = mins[select.value]
            colourMapper.high = maxs[select.value]
            source.change.emit()
            """,
        )

    from bokeh.models import HoverTool
    tooltips = [
        ('Index', '@' + indexName),
        ('Value', '@$name')
        ]
    tooltips.extend([(k.capitalize(), '@' + k) for k in nonVisKeys])
    hover = HoverTool(
        renderers = [patches],
        tooltips = tooltips
        )
    fig.add_tools(hover)

    slider.js_on_change('value', callback)
    select.js_on_change('value', callback)

    from bokeh.layouts import column, row
    layout = column(fig, row(select, slider))

    from bokeh.io import show

    show(layout)