import csv
import os
import ast
import os
import numpy as np
from datetime import datetime, timezone
import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame
import shapely
import mercantile

from fbapi.code import pull_datas

repoPath = os.path.abspath(os.path.dirname(__file__))

def default_proc(val):
    try:
        return ast.literal_eval(val)
    except:
        return val

def load_data(name, path = '.', ext = 'csv', _printSuppress = False, **procFuncs):
    header = []
    data = []
    dataPath = os.path.abspath(os.path.join(path, name))
    if not ext is None:
        dataPath += '.' + ext
    with open(dataPath, 'r') as f:
        r = csv.reader(f, delimiter = ',')
        rawheader = next(r)
        for key in rawheader:
            if key in procFuncs:
                if not procFuncs[key] is None:
                    header.append(key)
            else:
                header.append(key)
        for i, row in enumerate(r):
            outrow = []
            for key, val in zip(rawheader, row):
                try:
                    procFunc = procFuncs[key]
                    if not procFunc is None:
                        outrow.append(procFunc(val))
                except KeyError:
                    outrow.append(default_proc(val))
            data.append(outrow)
    if not _printSuppress:
        sample = list(zip(header, data[0]))
        print("*Printing 0th of {0} records*".format(len(data)))
        for row in sample: print(row[0] + ': ', row[1])
    return header, data

def load_datas(
        path = '.',
        ext = 'csv',
        superkeyName = 'superkey',
        superkeyProc = default_proc,
        _printSuppress = False,
        **procFuncs
        ):
    headers = []
    datas = []
    names = sorted([
        os.path.splitext(name)[0] \
            for name in os.listdir(path) \
                if os.path.splitext(name)[1].lstrip('.') == ext
        ])
    for name in names:
        header, data = load_data(
            name,
            path,
            ext,
            _printSuppress = True,
            **procFuncs
            )
        headers.append(header)
        datas.append(data)
    assert len(set([tuple(header) for header in headers])) == 1
    header = headers[0]
    header.append(superkeyName)
    for dNum, (name, data) in enumerate(zip(names, datas)):
        for rNum, row in enumerate(data):
            datas[dNum][rNum].append(superkeyProc(name))
    data = [item for sublist in datas for item in sublist]
    if not _printSuppress:
        sample = list(zip(header, data[0]))
        print("*Printing 0th of {0} records*".format(len(data)))
        for row in sample: print(row[0] + ': ', row[1])
    return header, data

def quadkey_to_poly(quadkey):
    x0, y0, x1, y1 = mercantile.bounds(mercantile.quadkey_to_tile(str(quadkey)))
    poly = shapely.geometry.Polygon([[x0, y0], [x0, y1], [x1, y1], [x1, y0]])
    return poly

def _process_datetime(x):
    stripped = datetime.strptime(x, '%Y-%m-%d-%H%M')
    adjusted = stripped.astimezone(timezone.utc)
    return adjusted
def _process_geometry(x):
    return shapely.wkt.loads(x)

FBDATA = {}
FBURLS = {}
for state in {'vic', 'nsw', 'qld', 'act', 'nt', 'sa', 'wa', 'tas'}:
    FBDATA[state] = dict()
    FBURLS[state] = dict()
    for dataset in {'pop', 'mob'}:
        FBDATA[state][dataset] = dict()
        FBURLS[state][dataset] = dict()
        for agg in {'tiles, regs'}:
            FBDATA[state][dataset][agg] = '_'.join(state, dataset, agg)
            FBURLS[state][dataset][agg] = None

FBURLS['vic']['pop']['tiles'] = '223808228714910'
FBURLS['vic']['mob']['tiles'] = '176962986764882'

def quick_pull_data(state, dataset, aggregation):
    global FBDATA
    global FBURLS
    rootURL = "https://www.facebook.com/geoinsights-portal/downloads"
    dataID = FBURLS[state][dataset][aggregation]
    dataURL = '/?id='.join([rootURL, dataID])
    print(dataURL)
    loginName = 'rohan.byrne@gmail.com'
    loginPass = 'Khaldun-1406!'
    dataDir = os.path.join(repoPath, 'data')
    outName = FBDATA[state][dataset][aggregation]
    outDir = os.path.abspath(os.path.join(dataDir, outName))
    dataMime = 'text/csv'
    outExt = '.csv'
    pull_datas(dataURL, loginName, loginPass, outDir, dataMime, outExt)

TZS = {
    'vic': 'Australia/Melbourne',
    'nsw': 'Australia/Sydney',
    'qld': 'Australia/Queensland',
    'nt': 'Australia/Darwin',
    'sa': 'Australia/Adelaide',
    'wa': 'Australia/Perth',
    'tas': 'Australia/Hobart',
    'act': 'Australia/Canberra'
    }

def get_fb_pop_tiles(state):
    quick_pull_data(state, 'pop', 'tiles')
    return load_fb_pop_tiles(state)
def get_fb_pop_tiles_vic():
    return get_fb_pop_tiles('vic')
def get_fb_pop_tiles_nsw():
    return get_fb_pop_tiles('nsw')
def get_fb_pop_tiles_qld():
    return get_fb_pop_tiles('qld')
def get_fb_pop_tiles_act():
    return get_fb_pop_tiles('act')
def get_fb_pop_tiles_nt():
    return get_fb_pop_tiles('nt')
def get_fb_pop_tiles_sa():
    return get_fb_pop_tiles('sa')
def get_fb_pop_tiles_wa():
    return get_fb_pop_tiles('wa')
def get_fb_pop_tiles_tas():
    return get_fb_pop_tiles('tas')

def get_fb_mob_tiles(state):
    quick_pull_data(state, 'mob', 'tiles')
    return load_fb_mob_tiles(state)
def get_fb_mob_tiles_vic():
    return get_fb_mob_tiles('vic')
def get_fb_pop_tiles_nsw():
    return get_fb_mob_tiles('nsw')
def get_fb_pop_tiles_qld():
    return get_fb_mob_tiles('qld')
def get_fb_pop_tiles_act():
    return get_fb_mob_tiles('act')
def get_fb_pop_tiles_nt():
    return get_fb_mob_tiles('nt')
def get_fb_pop_tiles_sa():
    return get_fb_mob_tiles('sa')
def get_fb_pop_tiles_wa():
    return get_fb_mob_tiles('wa')
def get_fb_pop_tiles_tas():
    return get_fb_mob_tiles('tas')

def load_fb_pop_tiles(state):
    global FBDATA
    dataDir = os.path.join(repoPath, 'data')
    subDir = FBDATA[state]['pop']['tiles']
    procFuncs = {
        'country': None,
        'date_time': None,
        'n_baseline': None,
        'n_difference': None,
        'density_baseline': None,
        'density_crisis': None,
        'percent_change': None,
        'clipped_z_score': None,
        'ds': None,
        'datetime': None,
        'quadkey': lambda x: int(x),
        'n_crisis': lambda x: int(x),
        'lat': None,
        'lon': None,
        }
    header, data = load_datas(
        os.path.join(dataDir, subDir),
        'csv',
        'datetime',
        _process_datetime,
        _printSuppress = True,
        **procFuncs
        )
    frm = df(data = data, columns = header)
    frm['geometry'] = frm.apply(
        lambda row: quadkey_to_poly(row['quadkey']),
        axis = 1
        )
    global TZS
    frm['datetime'].dt.tz_convert(TZS[state])
    frm = gdf(frm, geometry = 'geometry')
    frm = frm.rename({'n_crisis': 'n'}, axis = 1)
    frm = frm.set_index(['datetime', 'quadkey'])
    return frm
def load_fb_pop_tiles_vic():
    return load_fb_pop_tiles('vic')
def load_fb_pop_tiles_nsw():
    return load_fb_pop_tiles('nsw')
def load_fb_pop_tiles_qld():
    return load_fb_pop_tiles('qld')
def load_fb_pop_tiles_act():
    return load_fb_pop_tiles('act')
def load_fb_pop_tiles_nt():
    return load_fb_pop_tiles('nt')
def load_fb_pop_tiles_sa():
    return load_fb_pop_tiles('sa')
def load_fb_pop_tiles_wa():
    return load_fb_pop_tiles('wa')
def load_fb_pop_tiles_tas():
    return load_fb_pop_tiles('tas')

def load_fb_mob_tiles(state):
    global FBDATA
    dataDir = os.path.join(repoPath, 'data')
    subDir = FBDATA[state]['mob']['tiles']
    procFuncs = {
        'geometry': lambda x: shapely.wkt.loads(x),
        'date_time': None,
        'start_polygon_id': None,
        'start_polygon_name': None,
        'end_polygon_id': None,
        'end_polygon_name': None,
        'length_km': lambda x: float(x),
        'tile_size': None,
        'country': None,
        'level': None,
        'n_crisis': lambda x: int(x),
        'n_baseline': None,
        'n_difference': None,
        'percent_change': None,
        'is_statistically_significant': None,
        'z_score': None,
        'start_lat': None,
        'start_lon': None,
        'end_lat': None,
        'end_lon': None,
        'start_quadkey': lambda x: int(x),
        'end_quadkey': lambda x: int(x)
        }
    header, data = load_datas(
        os.path.join(dataDir, subDir),
        'csv',
        'datetime',
        _process_datetime,
        _printSuppress = True,
        **procFuncs
        )
    frm = df(data = data, columns = header)
    global TZS
    frm['datetime'].dt.tz_convert(TZS[state])
    frm = gdf(frm, geometry = 'geometry')
    frm = frm.rename({'n_crisis': 'n'}, axis = 1)
    frm = frm.rename({'start_quadkey': 'quadkey'}, axis = 1)
    frm = frm.set_index(['datetime', 'quadkey', 'end_quadkey'])
    return frm
def load_fb_mob_tiles_vic():
    return load_fb_mob_tiles('vic')
def load_fb_mob_tiles_nsw():
    return load_fb_mob_tiles('nsw')
def load_fb_mob_tiles_qld():
    return load_fb_mob_tiles('qld')
def load_fb_mob_tiles_act():
    return load_fb_mob_tiles('act')
def load_fb_mob_tiles_nt():
    return load_fb_mob_tiles('nt')
def load_fb_mob_tiles_sa():
    return load_fb_mob_tiles('sa')
def load_fb_mob_tiles_wa():
    return load_fb_mob_tiles('wa')
def load_fb_mob_tiles_tas():
    return load_fb_mob_tiles('tas')

def load_mobility_tiles(
        dataDir,
        subDir,
        tz = None # e.g. 'Australia/Melbourne'
        ):
    procFuncs = {
        'date_time': None,
        'tile_size': None,
        'country': None,
        'level': None,
        'n_baseline': None,
        'n_difference': None,
        'percent_change': None,
        'is_statistically_significant': None,
        'z_score': None,
        'start_lat': None,
        'start_lon': None,
        'end_lat': None,
        'end_lon': None,
        'datetime': None,
        'start_polygon_id': None,
        'start_polygon_name': None,
        'end_polygon_id': None,
        'end_polygon_name': None,
        'length_km': None,
        'n_crisis': lambda x: float(x) if not type(x) is str else 0.,
        }
    header, data = load_datas(
        os.path.join(dataDir, subDir),
        'csv',
        'datetime',
        _process_datetime,
        _printSuppress = True,
        **procFuncs
        )
    dataFrame = gdf(data, columns = header, geometry = 'geometry')
    if not tz is None:
        dataFrame['datetime'].dt.tz_convert(tz)
    return dataFrame

def load_lgas():
    paths = [repoPath, 'resources', 'LGA_2019_AUST.shp']
    lgaShapes = gpd.read_file(os.path.join(*paths))
    lgaShapes['LGA_CODE19'] = lgaShapes['LGA_CODE19'].astype(int)
    lgaShapes['STE_CODE16'] = lgaShapes['STE_CODE16'].astype(int)
    lgaLookup = lgaShapes.set_index('LGA_CODE19')
    return lgaLookup

def load_aus():
    paths = [repoPath, 'resources', 'AUS_2016_AUST.shp']
    ausFrame = gpd.read_file(os.path.join(*paths))
    return ausFrame

def load_SA4():
    paths = [repoPath, 'resources', 'SA4_2016_AUST.shp']
    saFrame = gpd.read_file(os.path.join(*paths))
    saFrame['SA4_CODE16'] = saFrame['SA4_CODE16'].astype(int)
    saFrame['STE_CODE16'] = saFrame['STE_CODE16'].astype(int)
    saFrame = saFrame.set_index('SA4_CODE16')
    saFrame = saFrame.loc[saFrame['AREASQKM16'] > 0.]
    return saFrame

def load_SA3():
    paths = [repoPath, 'resources', 'SA3_2016_AUST.shp']
    saFrame = gpd.read_file(os.path.join(*paths))
    saFrame['SA4_CODE16'] = saFrame['SA4_CODE16'].astype(int)
    saFrame['SA3_CODE16'] = saFrame['SA3_CODE16'].astype(int)
    saFrame['STE_CODE16'] = saFrame['STE_CODE16'].astype(int)
    saFrame = saFrame.set_index('SA3_CODE16')
    saFrame = saFrame.loc[saFrame['AREASQKM16'] > 0.]
    return saFrame

def load_SA2():
    paths = [repoPath, 'resources', 'SA2_2016_AUST.shp']
    saFrame = gpd.read_file(os.path.join(*paths))
    saFrame['SA4_CODE16'] = saFrame['SA4_CODE16'].astype(int)
    saFrame['SA3_CODE16'] = saFrame['SA3_CODE16'].astype(int)
    saFrame['SA2_5DIG16'] = saFrame['SA2_5DIG16'].astype(int)
    saFrame['SA2_MAIN16'] = saFrame['SA2_MAIN16'].astype(int)
    saFrame['STE_CODE16'] = saFrame['STE_CODE16'].astype(int)
    saFrame = saFrame.set_index('SA2_MAIN16')
    saFrame = saFrame.loc[saFrame['AREASQKM16'] > 0.]
    return saFrame

def load_SA1():
    paths = [repoPath, 'resources', 'SA1_2016_AUST.shp']
    saFrame = gpd.read_file(os.path.join(*paths))
    saFrame['SA4_CODE16'] = saFrame['SA4_CODE16'].astype(int)
    saFrame['SA3_CODE16'] = saFrame['SA3_CODE16'].astype(int)
    saFrame['SA2_5DIG16'] = saFrame['SA2_5DIG16'].astype(int)
    saFrame['SA2_MAIN16'] = saFrame['SA2_MAIN16'].astype(int)
    saFrame['SA1_7DIG16'] = saFrame['SA1_7DIG16'].astype(int)
    saFrame['SA1_MAIN16'] = saFrame['SA1_MAIN16'].astype(int)
    saFrame['STE_CODE16'] = saFrame['STE_CODE16'].astype(int)
    saFrame = saFrame.set_index('SA1_MAIN16')
    saFrame = saFrame.loc[saFrame['AREASQKM16'] > 0.]
    return saFrame

def load_states(trim = True):
    paths = [repoPath, 'resources', 'STE_2016_AUST.shp']
    frm = gpd.read_file(os.path.join(*paths))
    frm['STE_CODE16'] = frm['STE_CODE16'].astype(int)
    frm = frm.set_index('STE_NAME16')
    if trim:
        frm = frm.drop('Other Territories')
    return frm

def load_mb(state, trim = True):
    filename = "MB_2016_{0}.shp".format(state)
    paths = [repoPath, 'resources', filename]
    frm = gpd.read_file(os.path.join(*paths))
    frm['MB_CODE16'] = frm['MB_CODE16'].astype(int)
    frm['SA1_MAIN16'] = frm['SA1_MAIN16'].astype(int)
    frm['SA1_7DIG16'] = frm['SA1_7DIG16'].astype(int)
    frm['SA2_MAIN16'] = frm['SA2_MAIN16'].astype(int)
    frm['SA2_5DIG16'] = frm['SA2_5DIG16'].astype(int)
    frm['SA3_CODE16'] = frm['SA3_CODE16'].astype(int)
    frm['SA4_CODE16'] = frm['SA4_CODE16'].astype(int)
    frm['STE_CODE16'] = frm['STE_CODE16'].astype(int)
    frm = frm.set_index('MB_CODE16')
    if trim:
        frm = frm.drop(frm.loc[frm['geometry'] == None].index)
    return frm
def load_mb_vic(): return load_mb('VIC')
def load_mb_act(): return load_mb('ACT')
def load_mb_nsw(): return load_mb('NSW')
def load_mb_nt(): return load_mb('NT')
def load_mb_qld(): return load_mb('QLD')
def load_mb_sa(): return load_mb('SA')
def load_mb_tas(): return load_mb('TAS')
def load_mb_wa(): return load_mb('WA')