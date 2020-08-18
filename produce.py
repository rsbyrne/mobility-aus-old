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
        frm = frm[['name', 'area']]
        frm['type'] = source
        frm.index.name = 'code'
        frms.append(frm)
    frm = pd.concat(frms)
    frm = frm.sort_index()
    pops = []
    if 'lga' in sources:
        pops.append(load.load_lga_pop().rename(dict(LGA_code_2018 = 'code'), axis = 1).set_index('code')['ERP_2018'])
    if 'sa2' in sources:
        pops.append(load.load_sa2_pop().rename(dict(SA2_maincode_2016 = 'code'), axis = 1).set_index('code')['ERP_2018'])
    if len(pops):
        popCodes = pd.concat(pops)
        frm['pop'] = popCodes
    return frm

def make_mob_plots(frm, region, aggType = 'lga'):

    agg = lambda key: frm.reset_index().groupby(key).apply(
        lambda x: (x['stay'] * x['weight'] / x['weight'].sum()).sum()
        )
    dateAvs = agg('date')
    regionAvs = agg('code')

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
    assert len(agg)

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
#     frm['weight'] = frm['n'] / frm.reset_index().groupby('date')['n'].aggregate(sum)
    frm['weight'] = frm['n'] / frm['n'].sum()
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

def get_melvic_bokeh_frm():

    import analysis

    frm = analysis.make_melvic_dataFrm()
    cases = analysis.make_casesFrm()
    dates = sorted(set(frm.index.get_level_values('date')))
    cases = cases.loc[pd.IndexSlice[dates, :]]
    dataFrm = frm
    lgas = load.load_lgas()
    lgas.index = lgas.index.astype(str)

    frm = dataFrm.copy()
    frm = frm.reset_index().set_index(['date', 'name'])
    frm = frm[['km', 'adjstay', 'visit', 'stayscore', 'pop']]
    frm = frm.rename(dict(adjstay = 'stay', stayscore = 'score'), axis = 1)
    frm['active'] = (cases['ACTIVE_CNT'] * 10000 / frm['pop']).fillna(0.)
    serieses = dict()
    weightKey = 'pop'
    level = 'date'
    for key in ['km', 'stay', 'visit', 'active']:
        fn = lambda f: np.average(f[key], weights = f[weightKey])
        series = frm[[key, weightKey]].groupby(level = level).apply(fn)
        serieses[key] = series
    avFrm = df(serieses)
    avFrm['score'] = analysis.get_stayscore_series(avFrm['stay'])
    avFrm['name'] = 'average'
    avFrm = avFrm.reset_index().set_index(['date', 'name'])
    frm = frm.drop('pop', axis = 1)
    frm = frm.append(avFrm)
    frm = frm.sort_index(axis = 0).sort_index(axis = 1)
    frm.columns.name = 'variables'
    masterFrm = frm

    geometry = lgas.reset_index() \
        .rename(dict(LGA_CODE19 = 'code'), axis = 1) \
        .set_index('code')['geometry']
    codenames = dict(zip(dataFrm.index.get_level_values(1), dataFrm['name']))
    geometry = geometry.drop([i for i in geometry.index if not i in codenames])
    geometry.index = [codenames[i] for i in geometry.index]
    masterGeometry = geometry

    return masterFrm, masterGeometry

def bokeh_spacetimepop(
        frm,
        geometry,
        title = '',
        preamble = '',
        varNames = None,
        varNotes = dict(),
        pw = 700,
        ph = 700,
        xZones = dict(),
        ):

    import numpy as np

    import pandas as pd
    df = pd.DataFrame
    idx = pd.IndexSlice
    import geopandas as gpd
    gdf = gpd.GeoDataFrame

    from bokeh.models import ColumnDataSource, HoverTool, Legend, LegendItem, CDSView, IndexFilter
    from bokeh.plotting import figure, show
    from bokeh.io import output_notebook

    #     frm = frm.reset_index().pivot(index = frm.index.names[0], columns = frm.index.names[1])
    frm = frm.copy()
    frm = frm.sort_index()
    #     geometry = geometry.copy()

    from bokeh.models import Div

    title = f'<h1>{title}</h1>'
    title = Div(
        text = title,
        width = pw,
        )
    preamble = Div(
        text = preamble,
        width = pw,
        )

    if varNames is None:
        varNames = frm.columns.sort_values()
        varMetaName = varNames.name
    else:
        varMetaName = 'variable'
    varNames = list(varNames)
    seriesNames = frm.index.levels[1].sort_values()
    seriesMetaName = seriesNames.name
    seriesNames = list(seriesNames)
    dates = [str(int(round(i.to_numpy().astype(int) / 1e6))) for i in frm.index.levels[0]]
    frm.index = frm.index.set_levels(dates, level = 0)
    defaultVar = varNames[0]
    defaultDate = dates[-1]
    pivotFrm = frm.reset_index() \
        .pivot(index = frm.index.names[0], columns = frm.index.names[1]) \
        .sort_index()

    defaultVar = varNames[0]
    defaultDate = dates[-1]

    for key in varNames:
        if not key in varNotes:
            varNotes[key] = ''
        else:
            varNotes[key] = f'<i>{varNotes[key]}</i>'

    varNote = Div(
        text = varNotes[defaultVar],
        width = pw - 120,
        )

    lineSources = {
        key: ColumnDataSource(pivotFrm[key])
            for key in pivotFrm.columns.levels[0]
        }
    lineSource = ColumnDataSource(pivotFrm[defaultVar])
    lineSource.name = defaultVar

    barSources = dict()
    for varName in varNames:
        for index, date in zip(sorted(pivotFrm.index), dates):
            series = pivotFrm.loc[index, varName]
            subFrm = df(dict(
                name = series.index,
                value = series.values,
                height = abs(series.values),
                offset = series.values / 2.
                ))
            barSources[varName + '_' + date] = ColumnDataSource(subFrm)
    barSource = ColumnDataSource(barSources[defaultVar + '_' + defaultDate].data)
    barSource.name = ', '.join([str(defaultVar), str(defaultDate)])

    bounds = geometry.bounds
    minx = np.min(bounds['minx'])
    maxx = np.max(bounds['maxx'])
    miny = np.min(bounds['miny'])
    maxy = np.max(bounds['maxy'])
    aspect = (maxx - minx) / (maxy - miny)
    from shapely.geometry import Polygon
    import itertools
    corners = list(itertools.product(geometry.total_bounds[::2], geometry.total_bounds[1::2]))
    allPoly = Polygon([corners[0], corners[1], corners[3], corners[2]])
    allPoly = allPoly.centroid.buffer(np.sqrt(allPoly.area) / 1e6)
    geometry['average'] = allPoly
    geometry = geometry.simplify(np.sqrt(geometry.area).min() * 10. ** 3.5)
    geoFrm = frm.reset_index().pivot(index = frm.index.names[1], columns = frm.index.names[0])
    geoFrm.columns = geoFrm.columns.map('_'.join).str.strip('_')
    geoFrm['geometry'] = geometry
    geoFrm = gdf(geoFrm)
    from bokeh.models import GeoJSONDataSource
    geoJSON = geoFrm.reset_index().to_json()
    geoSource = GeoJSONDataSource(geojson = geoJSON)
    mins = {n: frm[n].min() for n in varNames}
    maxs = {n: frm[n].max() for n in varNames}

    xName = frm.index.names[0]

    lineFig = figure(
        x_axis_type = 'datetime',
        y_range = (mins[defaultVar], maxs[defaultVar]),
        plot_height = int((ph - 100) * 1. / 2.),
        plot_width = pw,
        toolbar_location = 'left',
        tools = 'save, pan, box_zoom, reset, xwheel_zoom',
        active_scroll = 'auto',
    #         title = title,
        )

    barFig = figure(
        x_range = seriesNames,
        plot_height = int((ph - 100) * 1. / 2.),
        plot_width = pw,
    #         title = "Scores on my birthday",
        toolbar_location = None,
        tools = ""
        )
    barFig.xgrid.grid_line_color = None
    barFig.xaxis.major_label_orientation = 'vertical'

    mapFig = figure(
        plot_width = pw - 20,
        plot_height = int(round((pw - 20) / aspect)),
        toolbar_location = 'right',
        tools = 'pan, zoom_in, zoom_out, wheel_zoom, reset',
        background_fill_color = "lightgrey"
        )
    mapFig.xgrid.grid_line_color = None
    mapFig.ygrid.grid_line_color = None

    from matplotlib.pyplot import get_cmap
    from matplotlib.colors import rgb2hex
    cmap = get_cmap('nipy_spectral')
    cs = [rgb2hex(cmap(i / len(seriesNames), alpha = 0.5)) for i in range(len(seriesNames))]

    lines = []

    for seriesName, colour in zip(seriesNames, cs):

        line = lineFig.line(
            xName,
            seriesName,
            source = lineSource,
            color = colour,
            alpha = 0.8,
            muted_color = 'gray',
            muted_alpha = 0.3,
            muted = True,
            line_width = 2,
    #             legend_label = seriesName,
            )

        from bokeh.models import HoverTool
        lineFig.add_tools(HoverTool(
            renderers = [
                line,
                ],
            tooltips = [
                (seriesMetaName.capitalize(), seriesName),
                (xName.capitalize(), f'@{xName}' + '{%Y-%m-%d}'),
                ('Value', f'@{{{seriesName}}}'),
                ],
            formatters = {
                f'@{xName}': 'datetime',
                seriesName: 'numeral',
                },
            toggleable = False
            ))

        lines.append(line)

    bars = []
    for i, (seriesName, colour) in enumerate(zip(seriesNames, cs)):
        view = CDSView(source = barSource, filters = [IndexFilter([i,]),])
        bar = barFig.rect(
            source = barSource,
            view = view,
            x = 'name',
            y = 'offset',
            height = 'height',
            width = 0.9,
            color = colour,
            muted_color = 'gray',
            muted_alpha = 0.3,
            muted = True,
            )
        bars.append(bar)

    from bokeh.palettes import Viridis256
    from bokeh.models import LinearColorMapper, ColorBar
    palette = Viridis256
    mapColourMapper = LinearColorMapper(
        palette = palette,
        low = frm.loc[idx[defaultDate, :], defaultVar].min(),
        high = frm.loc[idx[defaultDate, :], defaultVar].max(),
        )
    mapColourBar = ColorBar(
        color_mapper = mapColourMapper, 
        label_standoff = 8,
        width = 30,
        height = int(round(mapFig.plot_height * 0.9)),
        border_line_color = None,
        location = (0, 0), 
        orientation = 'vertical',
        )
    mapFig.add_layout(mapColourBar, 'left')

    patches = []
    for i, seriesName in enumerate(seriesNames):
        view = CDSView(source = geoSource, filters = [IndexFilter([i,]),])
        patch = mapFig.patches(
            'xs',
            'ys',
            source = geoSource,
            view = view,
            fill_color = dict(
                field = '_'.join([defaultVar, defaultDate]),
                transform = mapColourMapper,
                ),
            line_color = 'grey', 
            line_width = 0.25,
            fill_alpha = 0.,
            name = '_'.join([defaultVar, defaultDate])
            )
        patches.append(patch)

    from bokeh.models import HoverTool
    mapHover = HoverTool(
        renderers = patches,
        tooltips = [
            (seriesMetaName.capitalize(), f'@{seriesMetaName}'),
            ('Value', '@$name'),
            ]
        )
    mapFig.add_tools(mapHover)

    from bokeh.models import BoxAnnotation
    from bokeh.models import Label
    for name, zone in xZones.items():
        convD = lambda x: int(round(pd.Timestamp(x).to_numpy().astype(int) / 1e6))
        left, right = [None if val is None else convD(val) for val in zone]
        zone = BoxAnnotation(
            left = left,
            right = right,
            fill_alpha = 0.1,
            fill_color = 'gray',
            )
        zoneLabel = Label(
            text = name + ' (end)' if left is None else name,
            text_font_size = '8pt',
            x = right if left is None else left,
            y = 10,
            x_units = 'data',
            y_units = 'screen',
            angle = -90 if left is None else 90,
            angle_units = 'deg',
            x_offset = -10 if left is None else 10,
            y_offset = 5 * (len(name) + 6) if left is None else 0
            )
        lineFig.add_layout(zone)
        lineFig.add_layout(zoneLabel)

    from bokeh.models import Span
    span = Span(
        location = int(defaultDate),
        dimension = 'height',
        line_color = 'red',
    #         line_dash = 'dashed',
        line_width = 1
        )
    lineFig.add_layout(span)

    from bokeh.models.widgets import DateSlider
    slider = DateSlider(
        title = 'Date',
        start = int(dates[0]),
        end = int(dates[-1]),
        step = int(8.64 * 1e7), # days
        value = int(defaultDate),
        width = pw - 60,
        align = 'end'
        )

    from bokeh.models.widgets import Select
    select = Select(
        title = "Choose data:",
        options = varNames,
        value = defaultVar,
        width = 100,
        )

    from bokeh.models import CheckboxGroup
    checkboxes = CheckboxGroup(
        labels = seriesNames,
        active = [],
        )
    checkboxAll = CheckboxGroup(
        labels = ['All',],
        active = [],
        )

    from bokeh.models import CustomJS
    callback = CustomJS(
        args = dict(
            y_range = lineFig.y_range,
            lineSources = lineSources,
            lineSource = lineSource,
            barSources = barSources,
            barSource = barSource,
            bars = bars,
            lines = lines,
            patches = patches,
            select = select,
            slider = slider,
            span = span,
            checkboxes = checkboxes,
            varNote = varNote,
            varNotes = varNotes,
            geoSource = geoSource,
            mapColourMapper = mapColourMapper,
            mins = mins,
            maxs = maxs,
            ),
        code = """
            lineSource.data = lineSources[select.value].data
            lineSource.name = select.value
            lineSource.change.emit()
            span.location = slider.value
            span.change.emit()
            y_range.setv({'start': mins[select.value], 'end': maxs[select.value]})
            varNote.text = varNotes[select.value]
            varNote.change.emit()
            const barChoice = select.value + '_' + slider.value
            barSource.data = barSources[barChoice].data
            barSource.name = select.value.toString() + ', ' + slider.value.toString()
            barSource.change.emit()
            for (let i = 0; i < lines.length; i++){
                let checked = checkboxes.active.includes(i)
                lines[i].muted = !(checked)
                bars[i].muted = !(checked)
                var alpha = checked ? 1 : 0;
                patches[i].glyph.fill_alpha = alpha
            }
            const newCol = select.value + '_' + slider.value
            for (let i = 0; i < lines.length; i++){
                patches[i].glyph.fill_color['field'] = newCol
                patches[i].name = newCol
            }
            mapColourMapper.low = mins[select.value]
            mapColourMapper.high = maxs[select.value]
            geoSource.change.emit()
            """,
        )

    allCheckCallback = CustomJS(
        args = dict(
            lines = lines,
            checkboxes = checkboxes,
            checkboxAll = checkboxAll,
            callback = callback
            ),
        code = """
            checkboxes.active.length = 0
            if (checkboxAll.active.length > 0) {
                let arr = []
                for (let i = 0; i < lines.length; i++){
                    arr.push(i)
                    }
                checkboxes.active.push(...arr)
            }
            checkboxes.change.emit()
            callback.execute()
            """
        )

    slider.js_on_change('value', callback)
    select.js_on_change('value', callback)
    checkboxes.js_on_change('active', callback)
    checkboxAll.js_on_change('active', allCheckCallback)

    from bokeh.layouts import column, row
    layout = column(
        title,
        preamble,
        row(select, varNote),
        row(column(lineFig, slider, barFig), column(checkboxes, checkboxAll)),
        mapFig
        )

    return layout

def make_meldash(returnPlot = False):
    frm, geometry = get_melvic_bokeh_frm()
    myplot = bokeh_spacetimepop(
        frm,
        geometry = geometry,
        title = 'Mobility During COVID - Melbourne Councils',
        preamble = """
            These plots, based on Facebook location tracking data,
            show the <b>changes in patterns of movement</b>
            of tens of thousands of anonymous Facebook users
            in response to the COVID-19 pandemic.
            The data has been aggregated to <b>Local Government Areas</b>,
            typically city councils,
            and goes back as far as mid-April when collection began.
            Full data, including for other regions, is available
            <a href="https://rsbyrne.github.io/mobility-aus/">here</a>.
            The data are updated daily and the portal is continually being improved.
            If you have questions or suggestions, please contact
            <a href="mailto:rohan.byrne@unimelb.edu.au">Rohan Byrne</a>.
            """,
        varNotes = {
            'active': """
                This shows the number of active cases in each council
                as of that day per ten thousand people.
                """,
            'km': """
                This shows the average distance travelled
                by Facebook users observed moving
                from a particular council area on a particular day.
                """,
            'score': """
                This is an estimate  of lockdown compliance
                where one or higher is very good and zero or lower is very bad;
                it is calculated by normalising the Facebook 'stay' percentages
                with respect to the highest and lowest records
                observed for that day of the week (e.g. 'all Mondays')
                in that council.
                """,
            'stay': """
                This represents the proportion of Facebook records
                for a particular day and council
                which showed no sign of movement
                (either because no-one went anywhere at all,
                or because the journeys they did make were too small,
                or too brief,
                or too fast,
                or made by too few people for Facebook to collect them.)
                """,
            'visit': """
                This shows the proportion of all travellers on a given day
                who travelled to destinations within a given council area.
                """,
            },
        xZones = {
            "First Lockdown": (None, '2020-05-13'),
            "Queen's Birthday": ('2020-06-07', '2020-06-09'),
            "School holidays": ('2020-06-26', '2020-07-20'),
            "Second lockdown": ('2020-07-09', None),
            "Stage Four": ('2020-08-02', None),
            },
        pw = 700,
        ph = 700,
        )

    import os
    from bokeh.io import output_file, show
    name = 'meldash'
    outFilename = name + '.html'
    outPath = os.path.join(repoPath, 'products', outFilename)
    if os.path.isfile(outPath):
        os.remove(outPath)
    output_file(outPath, title = 'Melbourne COVID dashboard')
    show(myplot)

    if returnPlot:
        return myplot