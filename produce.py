import numpy as np
import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame

import load
import utils
import processing
import aggregate

import produce
import load

import numpy as np

import shapely
import mercantile

repoPath = os.path.abspath(os.path.dirname(__file__))

def get_mob_lga_date(region, refresh = False):
    name = region
    filename = '_'.join(['mob', 'lga', name]) + '.csv'
    filePath = os.path.join(repoPath, 'product', filename)
    if os.path.isfile(filePath) and not refresh:
        return pd.read_csv(filePath)
    else:
        out = make_mob_lga_date(region, refresh)
        out.to_csv(filePath)
        return out
def make_mob_lga_date(region, refresh = False):

    if refresh:
        mob = load.get_fb_mob_tiles(region)
    else:
        mob = load.load_fb_mob_tiles(region)

    lgas = load.load_lgas()
    agg = aggregate.aggregate_mob_tiles_to_regions(mob, lgas)
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

    frm = out
    if as_gdf or return_both:
        geoFrm = processing.frm_to_lgaFrm(frm, key = 'start')
        if return_both:
            return frm, geoFrm
        else:
            return geoFrm
    else:
        return frm

def make_mob_lga_dateMap(region, refresh = False):

    raw = make_mob_lga_date(region, refresh)
    pivoted = utils.pivot(raw, 'start', 'date', 'stay')
    pivoted = pivoted['stay']

    frm = pivoted.copy()
    indexNames = frm.index.names
    frm = frm.reset_index()
    lgas = load.load_lgas()
    frm['geometry'] = frm['start'].apply(lambda x: lgas.loc[x]['geometry'])
    frm = frm.set_index(indexNames)
    frm = gdf(frm)
    frm['name'] = lgas.loc[frm.index]['LGA_NAME19']
    frm['area'] = lgas.loc[frm.index]['AREASQKM19']

    scale = np.sqrt(np.min(frm['geometry'].area))
    frm['geometry'] = frm['geometry'].simplify(scale * 1e-1)
    frm['geometry'] = frm['geometry'].buffer(scale * 1e-1)

    frm.columns = [
        str(round(int(n.to_numpy()) / 1e6)) if type(n) is pd.Timestamp else n
            for n in frm.columns
        ]

    mapName = '_'.join(['mob', 'lga', region])

    make_dateMap(frm, mapName, size = 400)

def make_dateMap(frm, name, size = 400):

    path = repoPath

    minx = np.min(frm.bounds['minx'])
    maxx = np.max(frm.bounds['maxx'])
    miny = np.min(frm.bounds['miny'])
    maxy = np.max(frm.bounds['maxy'])
    aspect = (maxx - minx) / (maxy - miny)

    ts = [n for n in frm.columns if n.isnumeric()]

    allMin = frm[ts].min().min()
    allMax = frm[ts].max().max()

    from bokeh.models import GeoJSONDataSource
    geoJSON = frm.to_json()
    source = GeoJSONDataSource(geojson = geoJSON)

    from bokeh.io import output_file
    outFilename = name + '.html'
    outDir = os.path.abspath(path)
    outPath = os.path.join(outDir, outFilename)
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

    from bokeh.palettes import brewer
    from bokeh.models import LinearColorMapper, ColorBar
    palette = brewer['RdBu'][10]
    colourMapper = LinearColorMapper(
        palette = palette,
        low = allMin,
        high = allMax,
        )
    colourBar = ColorBar(
        color_mapper = colourMapper, 
        label_standoff = 8,
        width = int(round(aspect * size / 3.)),
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