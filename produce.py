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

def make_mob_plots(frm, region):

    frm = frm.reset_index()
    func = lambda x: (x['stay'] * x['n']).sum() / x['n'].sum()
    dateAvs = frm.groupby('date')[['n', 'stay']].apply(func)
    regionAvs = frm.groupby('start')[['n', 'stay']].apply(func)

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

    filename = '_'.join(['mob', 'lga', region]) + '.png'
    filePath = os.path.join(repoPath, 'products', filename)
    fig.savefig(filePath)

def get_mob_lga_date(region, refresh = False, get = False):
    filename = '_'.join(['mob', 'lga', region]) + '.csv'
    filePath = os.path.join(repoPath, 'products', filename)
    if os.path.isfile(filePath) and not refresh:
        out = pd.read_csv(filePath)
        out['date'] = pd.to_datetime(out['date'])
        out = out.set_index(['date', 'start'])
        return out
    else:
        out = make_mob_lga_date(region, get)
        out.to_csv(filePath)
        return out
def make_mob_lga_date(region, get = False, override = False):

    mob = load.load_fb_tiles(region, 'mob', get = get, override = override)

    agg = aggregate.aggregate_mob_tiles_to_lgas(mob, region)
    agg = aggregate.aggregate_by_date(agg)

    frm = agg.copy()
    frm = frm.reset_index()
    frm['n'] *= frm['weight']
    frm['km'] *= frm['n']
    frm.loc[frm['km'] == 0., 'stay'] = frm['n']
    frm = frm.set_index(['date', 'start'])
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
    frm['km'] /= frm['n']
    out = frm
    
    return out

def make_mob_lga_dateMap(raw, region):

    frm = raw.copy()
    frm['km'] = frm['km'].apply(lambda x: max([x, 1e-3]))
    frm['log10km'] = np.log10(frm['km'])
    frm = utils.pivot(frm, 'start', 'date', 'log10km')
    frm = frm['log10km']
    pivoted = frm

    frm = pivoted.copy()
    indexNames = frm.index.names
    frm = frm.reset_index()
    lgas = load.load_lgas()
    frm['geometry'] = frm['start'].apply(lambda x: lgas.loc[x]['geometry'])
    frm = frm.set_index(indexNames)
    frm = gdf(frm)
    frm['name'] = lgas.loc[frm.index]['LGA_NAME19']
    frm['area'] = lgas.loc[frm.index]['AREASQKM19']

    if len(frm) > 25:
        scale = np.sqrt(np.median(frm['geometry'].area))
        scalingCoeff = len(frm) * 1e-2
        frm['geometry'] = frm['geometry'].simplify(scale * scalingCoeff)
        frm['geometry'] = frm['geometry'].buffer(scale * 0.5 * scalingCoeff)

    frm.columns = [
        str(round(int(n.to_numpy()) / 1e6)) if type(n) is pd.Timestamp else n
            for n in frm.columns
        ]

    mapName = '_'.join(['mob', 'lga', region])

    make_dateMap(frm, mapName, size = 600)

def make_dateMap(frm, name, size = 600):

    minx = np.min(frm.bounds['minx'])
    maxx = np.max(frm.bounds['maxx'])
    miny = np.min(frm.bounds['miny'])
    maxy = np.max(frm.bounds['maxy'])
    aspect = (maxx - minx) / (maxy - miny)

    ts = [n for n in frm.columns if n.isnumeric()]
    assert len(ts)

    allMin = frm[ts].min().min()
    allMax = frm[ts].max().max()

    from bokeh.models import GeoJSONDataSource
    geoJSON = frm.to_json()
    source = GeoJSONDataSource(geojson = geoJSON)

    from bokeh.io import output_file
    outFilename = name + '.html'
    outPath = os.path.join(repoPath, 'products', outFilename)
    if os.path.isfile(outPath):
        os.remove(outPath)
    output_file(outPath)

    from bokeh.plotting import figure
    fig = figure(
        title = name,
        plot_height = size,
        plot_width = int(round(size * aspect)), 
        toolbar_location = 'right',
        tools = 'pan, wheel_zoom, box_zoom, reset',
        background_fill_color = "lightgrey"
        )

    fig.xgrid.grid_line_color = None
    fig.ygrid.grid_line_color = None

    from bokeh.palettes import Viridis10
    from bokeh.models import LinearColorMapper, ColorBar
    palette = Viridis10[::-1]
    colourMapper = LinearColorMapper(
        palette = palette,
        low = allMin,
        high = allMax,
        )
    colourBar = ColorBar(
        color_mapper = colourMapper, 
        label_standoff = 8,
        width = int(round(aspect * size * 0.8)),
        height = int(round(size / 30)),
        border_line_color = None,
        location = (0, 0), 
        orientation = 'horizontal',
        )
    fig.add_layout(colourBar, 'below')

    patches = fig.patches(
        'xs',
        'ys',
        source = source,
        fill_color = dict(
            field = ts[-1],
            transform = colourMapper,
            ),
        line_color = 'grey', 
        line_width = 0.25,
        fill_alpha = 1
        )

    from bokeh.models.widgets import DateSlider as Slider
    slider = Slider(
        title = 'date',
        start = int(ts[0]),
        end = int(ts[-1]),
        step = int(8.64 * 1e7),
        value = int(ts[-1]),
        )

    from bokeh.models import CustomJS
    callback = CustomJS(
        args = dict(patches = patches, source = source, slider = slider),
        code = """
            patches.glyph.fill_color['field'] = String(slider.value)
            source.change.emit()
            """,
        )

    slider.js_on_change('value', callback)

    from bokeh.layouts import column, row
    layout = column(fig, slider)

    from bokeh.models import HoverTool
    fig.add_tools(HoverTool(
        renderers = [patches],
        tooltips = [
            ('LGA','@name'),
            ('Area', '@area'),
            ]
        ))

    from bokeh.io import show

    show(layout)