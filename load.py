import csv
import os
import ast
import os
import json
import numpy as np
from datetime import datetime, timezone
import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame
import shapely
import mercantile
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import itertools

import utils
from utils import quadkey_to_poly, standardise_timestamp, flip_quadkey

from fbapi.code import pull_datas

repoPath = os.path.abspath(os.path.dirname(__file__))

def default_proc(val):
    try:
        return ast.literal_eval(val)
    except:
        return val

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
        for agg in {'tiles', 'regs'}:
            FBDATA[state][dataset][agg] = '_'.join([state, dataset, agg])
            FBURLS[state][dataset][agg] = None

FBURLS['vic']['pop']['tiles'] = '223808228714910'
FBURLS['vic']['pop']['regs'] = '585468802067851'
FBURLS['vic']['mob']['tiles'] = '176962986764882'
FBURLS['vic']['mob']['regs'] = '981514028938434'
FBURLS['nsw']['pop']['tiles'] = '658468688050630'
FBURLS['nsw']['pop']['regs'] = '596832157845704'
FBURLS['nsw']['mob']['tiles'] = '529422397944028'
FBURLS['nsw']['mob']['regs'] = '648063726037889'
FBURLS['qld']['pop']['tiles'] = '237921380649272'
FBURLS['qld']['pop']['regs'] = '842807756209584'
FBURLS['qld']['mob']['tiles'] = '869575016889368'
FBURLS['qld']['mob']['regs'] = '266592891137969'
FBURLS['act']['pop']['tiles'] = None
FBURLS['act']['pop']['regs'] = None
FBURLS['act']['mob']['tiles'] = None
FBURLS['act']['mob']['regs'] = None
FBURLS['nt']['pop']['tiles'] = None
FBURLS['nt']['pop']['regs'] = None
FBURLS['nt']['mob']['tiles'] = None
FBURLS['nt']['mob']['regs'] = None
FBURLS['wa']['pop']['tiles'] = None
FBURLS['wa']['pop']['regs'] = None
FBURLS['wa']['mob']['tiles'] = None
FBURLS['wa']['mob']['regs'] = None
FBURLS['sa']['pop']['tiles'] = None
FBURLS['sa']['pop']['regs'] = None
FBURLS['sa']['mob']['tiles'] = None
FBURLS['sa']['mob']['regs'] = None
FBURLS['tas']['pop']['tiles'] = None
FBURLS['tas']['pop']['regs'] = None
FBURLS['tas']['mob']['tiles'] = None
FBURLS['tas']['mob']['regs'] = None

def quick_pull_data(state, dataset, aggregation):
    global FBDATA
    global FBURLS
    rootURL = "https://www.facebook.com/geoinsights-portal/downloads"
    dataID = FBURLS[state][dataset][aggregation]
    dataURL = '/?id='.join([rootURL, dataID])
    with open(os.path.join(repoPath, '.credentials.json'), 'r') as f:
        loginName, loginPass = json.load(f)
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

STATENAMES = {
    'vic': 'Victoria',
    'nsw': 'New South Wales',
    'qld': 'Queensland',
    'sa': 'South Australia',
    'wa': 'Western Australia',
    'tas': 'Tasmania',
    'nt': 'Northern Territory',
    'act': 'Australian Capital Territory'
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
def get_fb_mob_tiles_nsw():
    return get_fb_mob_tiles('nsw')
def get_fb_mob_tiles_qld():
    return get_fb_mob_tiles('qld')
def get_fb_mob_tiles_act():
    return get_fb_mob_tiles('act')
def get_fb_mob_tiles_nt():
    return get_fb_mob_tiles('nt')
def get_fb_mob_tiles_sa():
    return get_fb_mob_tiles('sa')
def get_fb_mob_tiles_wa():
    return get_fb_mob_tiles('wa')
def get_fb_mob_tiles_tas():
    return get_fb_mob_tiles('tas')

def load_fb_pop_tiles(state):
    return load_fb_tiles(state, 'pop')
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
    return load_fb_tiles(state, 'mob')
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

def load_fb_tiles(state, dataset):
    global FBDATA
    global TZS
    print("Preprocessing...")
    dataDir = os.path.join(repoPath, 'data')
    subDir = FBDATA[state][dataset]['tiles']
#     allFilePath = os.path.join(dataDir, subDir, 'all.shp')
    allFilePath = os.path.join(dataDir, subDir, '_all.csv')
    if os.path.isfile(allFilePath):
#         loaded = gdf.from_file(allFilePath)
        loaded = pd.read_csv(allFilePath)
        fix_dates = lambda t: pd.Timestamp(datetime.strptime(
            t.replace(':', ''),
            '%Y-%m-%d %H%M%S%z'
            ))
        fixedDates = {t: fix_dates(t) for t in set(loaded['datetime'])}
        loaded['datetime'] = loaded['datetime'].apply(lambda t: fixedDates[t])
        loaded['datetime'] = loaded['datetime'].dt.tz_convert(TZS[state])
        alreadyKeys = set([standardise_timestamp(t) for t in fixedDates.values()])
#         timestamps = set(loaded.reset_index()['datetime'])
#         alreadKeys = set([standardise_timestamp(t) for t in timestamps])
        loaded['quadkey'] = loaded['quadkey'].astype(str)
        if dataset == 'mob':
            loaded['end_key'] = loaded['end_key'].astype(str)
            loaded = loaded.set_index(['datetime', 'quadkey', 'end_key'])
        else:
            loaded = loaded.set_index(['datetime', 'quadkey'])
    else:
        loaded = None
        alreadyKeys = set()
    print("Loading files...")
    searchDir = os.path.join(dataDir, subDir)
    filenames = [
        n for n in os.listdir(searchDir) \
            if (n.endswith('.csv')) \
                and not (n.rstrip('.csv') in alreadyKeys or n[0] == '_')
        ]
    if not len(filenames):
        return loaded
    if dataset == 'mob':
        procFuncs = {
#             'geometry': lambda x: shapely.wkt.loads(x),
            'geometry': None,
            'date_time': None,
            'start_polygon_id': None,
            'start_polygon_name': None,
            'end_polygon_id': None,
            'end_polygon_name': None,
#             'length_km': lambda x: float(x),
            'length_km': None,
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
            'start_quadkey': lambda x: flip_quadkey(str(x), (False, True)),
            'end_quadkey': lambda x: flip_quadkey(str(x), (False, True))
            }
    elif dataset == 'pop':
        def _pop_handle_nan(x):
            if str(x) == '\\N':
                return 0.
            else:
                return float(x)
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
            'quadkey': lambda x: str(x),
            'n_crisis': _pop_handle_nan,
            'lat': None,
            'lon': None,
            }
    else:
        raise ValueError
    subFrms = []
    for filename in filenames:
        subFrm = pd.read_csv(os.path.join(searchDir, filename))
        dropKeys = [key for key, func in procFuncs.items() if func is None]
        subFrm = subFrm.drop(dropKeys, axis = 1)
        for key, func in procFuncs.items():
            if not func is None:
                subFrm[key] = subFrm[key].apply(func)
        subFrm['datetime'] = _process_datetime(filename.rstrip('.csv'))
        subFrms.append(subFrm)
        print('.')
    frm = pd.concat(subFrms)
    frm = frm.loc[frm['n_crisis'] > 0.]
    print("Processing...")
    if dataset == 'mob':
        frm = frm.rename(
            {'start_quadkey': 'quadkey', 'end_quadkey': 'end_key'},
            axis = 1
            )
    zoom = len(frm.iloc[0]['quadkey'])
    stateQuadkeys = load_state_quadkeys(state, zoom)
    frm = frm.drop(
        frm.loc[frm['quadkey'].apply(lambda x: x not in stateQuadkeys)].index
        )
#     quadPolys = {
#         q: quadkey_to_poly(q) \
#             for q in set(frm['quadkey'])
#         }
#     frm['geometry'] = frm['quadkey'].apply(lambda q: quadPolys[q])
#     frm = gdf(frm, geometry = 'geometry')
    frm['datetime'] = frm['datetime'].dt.tz_convert(TZS[state])
    frm = frm.rename({'n_crisis': 'n'}, axis = 1)
    if dataset == 'mob':
        frm = frm.set_index(['datetime', 'quadkey', 'end_key'])
    else:
        frm.set_index(['datetime', 'quadkey'])
    oldFrm = frm
    if not loaded is None:
        frm = pd.concat([loaded, frm])
    # saving:
#     toSave = frm.reset_index()
#     toSave['datetime'] = toSave['datetime'].apply(lambda x: str(x))
#     toSave.to_file(allFilePath)
    frm.to_csv(allFilePath)
    print("Done.")
    return frm

def load_quadkey_polys(quadkeys):
    quadkeys = set(quadkeys)
    quadPolys = {q: quadkey_to_poly(q) for q in quadkeys}
    frm = gdf(quadkeys, colu)

# def load_aggregation(state, dataset, aggregation):
#     frm = load_fb_tiles(state, dataset)
#     if aggregator == 'date':
#         frm = processing.aggregate_by_date(frm)

def load_lgas():
    paths = [repoPath, 'resources', 'LGA_2019_AUST.shp']
    lgaShapes = gpd.read_file(os.path.join(*paths))
    lgaShapes['LGA_CODE19'] = lgaShapes['LGA_CODE19'].astype(int)
    lgaShapes['STE_CODE16'] = lgaShapes['STE_CODE16'].astype(int)
    lgaLookup = lgaShapes.set_index('LGA_CODE19')
    lgaLookup = lgaLookup.dropna()
    return lgaLookup

def load_aus():
    paths = [repoPath, 'resources', 'AUS_2016_AUST.shp']
    ausFrame = gpd.read_file(os.path.join(*paths))
    return ausFrame

def load_SA(level):
    name = 'SA{0}_2016_AUST.shp'.format(str(level))
    if level in {4, 3}: keyRoot = 'SA{0}_CODE16'
    elif level in {2, 1}: keyRoot = 'SA{0}_MAIN16'
    else: raise ValueError
    key = keyRoot.format(str(level))
    paths = [repoPath, 'resources', name]
    frm = gpd.read_file(os.path.join(*paths))
    intCols = ['STE_CODE16', 'SA4_CODE16']
    if level < 4: intCols.append('SA3_CODE16')
    if level < 3: intCols.extend(['SA2_5DIG16', 'SA2_MAIN16'])
    if level < 2: intCols.extend(['SA1_7DIG16', 'SA1_MAIN16'])
    for intCol in intCols: frm[intCol] = frm[intCol].astype(int)
    frm = frm.set_index(key)
    frm = frm.loc[frm['AREASQKM16'] > 0.]
    frm = frm.dropna()
    return frm
def load_SA4(): return load_SA(4)
def load_SA3(): return load_SA(3)
def load_SA2(): return load_SA(2)
def load_SA1(): return load_SA(1)

def load_states(trim = True):
    paths = [repoPath, 'resources', 'STE_2016_AUST.shp']
    frm = gpd.read_file(os.path.join(*paths))
    frm['STE_CODE16'] = frm['STE_CODE16'].astype(int)
    frm = frm.set_index('STE_NAME16')
    if trim:
        frm = frm.drop('Other Territories')
    return frm
def load_state(name, **kwargs):
    global STATENAMES
    if name in STATENAMES:
        name = STATENAMES[name]
    return load_states(**kwargs).loc[name]['geometry']
def load_vic(): return load_state('vic')
def load_nsw(): return load_state('nsw')
def load_qld(): return load_state('qld')
def load_nt(): return load_state('nt')
def load_sa(): return load_state('sa')
def load_act(): return load_state('act')
def load_wa(): return load_state('wa')
def load_tas(): return load_state('tas')

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

def load_aus_pop():
    filePath = os.path.join(repoPath, 'resources', 'aus_pop_16.shp')
    if not os.path.isfile(filePath):
        return make_aus_pop()
    else:
        return gdf.from_file(filePath)
def make_aus_pop():
    openPath = os.path.join(repoPath, 'resources', 'apg16e_1_0_0.tif')
    with rasterio.open(openPath, 'r') as src:
        dst_crs = 'EPSG:4326'
        transform, width, height = calculate_default_transform(
            src.crs,
            dst_crs,
            src.width,
            src.height,
            *src.bounds
            )
        outArr, affine = reproject(
            source = src.read(1),
            destination = np.zeros((height, width)),
            src_transform = src.transform,
            src_crs = src.crs,
            dst_transform = transform,
            dst_crs = dst_crs,
            resampling = Resampling.nearest
            )
    data = outArr.flatten()
    combos = list(itertools.product(*[range(d) for d in outArr.shape]))
    data, combos = zip(*[(d, c) for d, c in zip(data, combos) if d > 0.])
    coords = np.array([affine * pair[::-1] for pair in combos])
    geometry = [shapely.geometry.Point(coord) for coord in coords]
    frm = gdf(
        data,
        columns = ['pop'],
        crs = 'epsg:4326',
        geometry = geometry
        )
    outPath = os.path.join(repoPath, 'resources', 'aus_pop_16.shp')
    frm.to_file(outPath)
    return frm

def load_gccs():
    openPath = os.path.join(repoPath, 'resources', 'gcc.shp')
    if os.path.isfile(openPath):
        frm = gdf.from_file(openPath)
        frm = frm.set_index('gcc')
        return frm
    return make_gccs()

def make_gccs():
    sa4 = load_SA4()
    gccs = sorted(set(sa4['GCC_NAME16']))
    geoms = []
    for gcc in gccs:
        region = shapely.ops.unary_union(
            sa4.set_index('GCC_NAME16').loc[gcc]['geometry']
            )
        region = region.buffer(np.sqrt(region.area) * 1e-3)
        geoms.append(region)
    frm = gdf(gccs, columns = ['gcc'], geometry = geoms)
    frm = frm.set_index('gcc')
    savePath = os.path.join(repoPath, 'resources', 'gcc.shp')
    frm.to_file(savePath)
    return frm

def load_state_quadkeys(state, zoom):
    filename = state + '_quadkeys' + str(zoom) + '.json'
    if not os.path.isfile(os.path.join(repoPath, 'resources', filename)):
        return make_state_quadkeys(state, zoom)
    with open(os.path.join(repoPath, 'resources',  filename), 'r') as f:
        return json.load(f)

def make_state_quadkeys(state, zoom):
    states = load_states(state)
    statePoly = states.loc['Victoria']['geometry']
    quadkeys = utils.find_quadkeys(statePoly, zoom, easy = False, soft = True)
    filename = state + '_quadkeys' + str(zoom) + '.json'
    with open(os.path.join(repoPath, 'resources',  filename), 'w') as f:
        json.dump(quadkeys, f)
    return quadkeys