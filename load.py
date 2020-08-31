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
sjoin = gpd.tools.sjoin
import shapely
import mercantile
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import itertools

import utils
from utils import quadkey_to_poly, standardise_timestamp, flip_quadkey

repoPath = os.path.abspath(os.path.dirname(__file__))

def default_proc(val):
    try:
        return ast.literal_eval(val)
    except:
        return val

def _process_datetime(x):
    stripped = datetime.strptime(x.replace(':', ''), '%Y-%m-%d %H%M')
    adjusted = stripped.astimezone(timezone.utc)
    return adjusted
def _process_geometry(x):
    return shapely.wkt.loads(x) 

FBDATA = {}
FBURLS = {}
regions = {
    'aus',
    'vic', 'mel',
    'nsw', 'syd',
    'qld', 'bri',
    'nt', 'dar',
    'act', 'can',
    'sa', 'ade',
    'wa', 'per',
    'tas', 'hob',
    }
for region in regions:
    FBDATA[region] = dict()
    FBURLS[region] = dict()
    for dataset in {'pop', 'mob'}:
        FBDATA[region][dataset] = dict()
        FBURLS[region][dataset] = dict()
        for agg in {'tiles', 'regs'}:
            FBDATA[region][dataset][agg] = '_'.join([region, dataset, agg])
            FBURLS[region][dataset][agg] = None

FBURLS['vic']['pop']['tiles'] = '223808228714910'
FBURLS['vic']['pop']['regs'] = '585468802067851'
FBURLS['vic']['mob']['tiles'] = '176962986764882'
FBURLS['vic']['mob']['regs'] = '981514028938434'
FBURLS['mel']['pop']['tiles'] = '1925466407588452'
FBURLS['mel']['pop']['regs'] = '565738300965768'
FBURLS['mel']['mob']['tiles'] = '2546450865611593'
FBURLS['mel']['mob']['regs'] = '701310510605369'

FBURLS['nsw']['pop']['tiles'] = '658468688050630'
FBURLS['nsw']['pop']['regs'] = '596832157845704'
FBURLS['nsw']['mob']['tiles'] = '529422397944028'
FBURLS['nsw']['mob']['regs'] = '648063726037889'
FBURLS['syd']['pop']['tiles'] = '2581274605535108'
FBURLS['syd']['pop']['regs'] = '2638111166453119'
FBURLS['syd']['mob']['tiles'] = '579800112886221'
FBURLS['syd']['mob']['regs'] = '269277164076139'

FBURLS['qld']['pop']['tiles'] = '237921380649272'
FBURLS['qld']['pop']['regs'] = '842807756209584'
FBURLS['qld']['mob']['tiles'] = '869575016889368'
FBURLS['qld']['mob']['regs'] = '266592891137969'
FBURLS['bri']['pop']['tiles'] = None
FBURLS['bri']['pop']['regs'] = None
FBURLS['bri']['mob']['tiles'] = None
FBURLS['bri']['mob']['regs'] = None

FBURLS['act']['pop']['tiles'] = None
FBURLS['act']['pop']['regs'] = None
FBURLS['act']['mob']['tiles'] = None
FBURLS['act']['mob']['regs'] = None
FBURLS['can']['pop']['tiles'] = None
FBURLS['can']['pop']['regs'] = None
FBURLS['can']['mob']['tiles'] = None
FBURLS['can']['mob']['regs'] = None

FBURLS['nt']['pop']['tiles'] = '265612204816107'
FBURLS['nt']['pop']['regs'] = '232940067975299'
FBURLS['nt']['mob']['tiles'] = '719906238817043'
FBURLS['nt']['mob']['regs'] = '236213960924061'
FBURLS['dar']['pop']['tiles'] = None
FBURLS['dar']['pop']['regs'] = None
FBURLS['dar']['mob']['tiles'] = None
FBURLS['dar']['mob']['regs'] = None

FBURLS['wa']['pop']['tiles'] = '1731649863641382'
FBURLS['wa']['pop']['regs'] = '1085292288522910'
FBURLS['wa']['mob']['tiles'] = '523885168292314'
FBURLS['wa']['mob']['regs'] = '261535465239826'
FBURLS['per']['pop']['tiles'] = '585492418979013'
FBURLS['per']['pop']['regs'] = '264128567940298'
FBURLS['per']['mob']['tiles'] = '636945033816336'
FBURLS['per']['mob']['regs'] = '2301294816837741'

FBURLS['sa']['pop']['tiles'] = '254460345740451'
FBURLS['sa']['pop']['regs'] = '347769182849254'
FBURLS['sa']['mob']['tiles'] = '302338520760065'
FBURLS['sa']['mob']['regs'] = '219876419306608'
FBURLS['ade']['pop']['tiles'] = '247296463128810'
FBURLS['ade']['pop']['regs'] = '547900422804131'
FBURLS['ade']['mob']['tiles'] = '217178312888286'
FBURLS['ade']['mob']['regs'] = '838313713317099'

FBURLS['tas']['pop']['tiles'] = '2370900323204701'
FBURLS['tas']['pop']['regs'] = '189120225461391'
FBURLS['tas']['mob']['tiles'] = '238484180822579'
FBURLS['tas']['mob']['regs'] = '256249448902015'
FBURLS['hob']['pop']['tiles'] = None
FBURLS['hob']['pop']['regs'] = None
FBURLS['hob']['mob']['tiles'] = None
FBURLS['hob']['mob']['regs'] = None

FBURLS['aus']['pop']['tiles'] = '220856239014922'
FBURLS['aus']['pop']['regs'] = '2848131948635964'
FBURLS['aus']['mob']['tiles'] = '3013895718671644'
FBURLS['aus']['mob']['regs'] = '156664265628571'

def quick_pull_data(state, dataset, aggregation):
    from fbapi.code import pull_datas
    rootURL = "https://www.facebook.com/geoinsights-portal/downloads"
    dataID = FBURLS[state][dataset][aggregation]
    dataURL = '/?id='.join([rootURL, dataID])
    with open(os.path.join(repoPath, '.credentials.json'), 'r') as f:
        loginName, loginPass = json.load(f)
    dataDir = os.path.join(repoPath, 'data')
    outName = FBURLS[state][dataset][aggregation]
    outDir = os.path.abspath(os.path.join(dataDir, outName))
    dataMime = 'text/csv'
    outExt = '.csv'
    pull_datas(dataURL, loginName, loginPass, outDir, dataMime, outExt)

TZS = {
    'vic': 'Australia/Melbourne',
    'mel': 'Australia/Melbourne',
    'nsw': 'Australia/Sydney',
    'syd': 'Australia/Sydney',
    'qld': 'Australia/Queensland',
    'bri': 'Australia/Brisbane',
    'nt': 'Australia/Darwin',
    'dar': 'Australia/Darwin',
    'sa': 'Australia/Adelaide',
    'ade': 'Australia/Adelaide',
    'wa': 'Australia/Perth',
    'per': 'Australia/Perth',
    'tas': 'Australia/Hobart',
    'hob': 'Australia/Hobart',
    'act': 'Australia/Canberra',
    'can': 'Australia/Canberra',
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

GCCNAMES = {
    'mel': 'Greater Melbourne',
    'syd': 'Greater Sydney'
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

def load_fb_tiles(region, dataset, get = False, override = False):
    global FBURLS
    if get:
        quick_pull_data(region, dataset, 'tiles')
    dataDir = os.path.join(repoPath, 'data')
    subDir = FBURLS[region][dataset]['tiles']
    searchDir = os.path.join(dataDir, subDir)
    if not os.path.isdir(searchDir):
        os.mkdir(searchDir, mode = 777)
    pre, ignoreKeys = None, set()
    if not override:
        try:
            pre, ignoreKeys = pre_load_fb_tiles(region, dataset)
        except FileNotFoundError:
            pass
    try:
        new = new_load_fb_tiles(region, dataset, ignoreKeys)
    except NoNewFiles:
        new = None
    if new is None and pre is None:
        raise NoData
    out = pd.concat([pre, new])
    out = out.sort_index()
    allFilePath = os.path.join(searchDir, '_all.csv')
    if os.path.exists(allFilePath):
        os.remove(allFilePath)
    out.to_csv(allFilePath)
    return out

def pre_load_fb_tiles(region, dataset):
    global FBURLS
    dataDir = os.path.join(repoPath, 'data')
    subDir = FBURLS[region][dataset]['tiles']
    searchDir = os.path.join(dataDir, subDir)
    allFilePath = os.path.join(searchDir, '_all.csv')
    if not os.path.isfile(allFilePath):
        raise FileNotFoundError(allFilePath)
    loaded = pd.read_csv(allFilePath)
    print("Fixing dates...")
    fix_dates = lambda t: pd.to_datetime(t, utc = True).tz_convert(TZS[region])
    fixedDates = {date: fix_dates(date) for date in set(loaded['datetime'])}
    loaded['datetime'] = loaded['datetime'].apply(lambda x: fixedDates[x])
    alreadyKeys = set([standardise_timestamp(t) for t in set(loaded['datetime'])])
    loaded['quadkey'] = loaded['quadkey'].astype(str)
    if dataset == 'mob':
        loaded['end_key'] = loaded['end_key'].astype(str)
        loaded = loaded.set_index(['datetime', 'quadkey', 'end_key'])
    else:
        loaded = loaded.set_index(['datetime', 'quadkey'])
    return loaded, alreadyKeys

class NoNewFiles(Exception):
    pass
class NoData(Exception):
    pass

def conditional_flip_quadkey(x):
    if str(x)[0] != '3':
        return flip_quadkey(str(x), (False, True))
    else:
        return str(x)

def new_load_fb_tiles(region, dataset, ignoreKeys = set()):
    if dataset == 'pop':
        raise Exception("Not implemented currently.")
    global FBURLS
    global TZS
    dataDir = os.path.join(repoPath, 'data')
    subDir = FBURLS[region][dataset]['tiles']
    searchDir = os.path.join(dataDir, subDir)
    filenames = [
        n for n in os.listdir(searchDir) \
            if (n.endswith('.csv')) \
                and not (n.rstrip('.csv') in ignoreKeys or n[0] == '_')
        ]
    if not len(filenames):
        raise NoNewFiles
    renameDict = {
        'start_quadkey': 'quadkey',
        'start_quad': 'quadkey',
        'end_quadkey': 'end_key',
        'end_quad': 'end_key',
        'date_time': 'datetime',
        'length_km': 'km',
        'n_crisis': 'n'
        }
    keepKeys = ['datetime', 'quadkey', 'end_key', 'km', 'n']
    procFuncs = {
        'datetime': _process_datetime,
        'km': float,
        'quadkey': str,
        'end_key': str,
        }
    print("Loading files...")
    frms = []
    for f in filenames:
        frm = pd.read_csv(os.path.join(searchDir, f))
        frm = frm.rename(mapper = renameDict, axis = 1)
        frm = frm[keepKeys]
        frms.append(frm)
    frm = pd.concat(frms)
    print("Processing...")
    for key, func in procFuncs.items():
        frm[key] = frm[key].apply(func)
    frm['datetime'] = frm['datetime'].dt.tz_convert(TZS[region])
    frm['quadkey'] = frm['quadkey'].apply(conditional_flip_quadkey)
    frm = frm.loc[frm['n'] > 0.]
    frm = frm.set_index(['datetime', 'quadkey', 'end_key'])
    print("Done.")
    return frm

def load_generic(option, **kwargs):
    optionsDict = {
        'lga': load_lgas,
        'sa2': lambda: load_SA(2),
        'postcodes': load_postcodes,
        }
    return optionsDict[option](**kwargs)

def load_lgas():
    paths = [repoPath, 'resources', 'LGA_2019_AUST.shp']
    lgas = gpd.read_file(os.path.join(*paths))
    lgas['LGA_CODE19'] = lgas['LGA_CODE19'].astype(int)
    lgas['STE_CODE16'] = lgas['STE_CODE16'].astype(int)
    lgas = lgas.set_index('LGA_CODE19')
    lgas = lgas.dropna()
    lgas['name'] = lgas['LGA_NAME19']
    lgas['area'] = lgas['AREASQKM19']
    return lgas

def load_postcodes():
    paths = [repoPath, 'resources', 'POA_2016_AUST.shp']
    frm = gpd.read_file(os.path.join(*paths))
    frm = frm.set_index('POA_CODE16')
    frm = frm.dropna()
    frm['name'] = frm['POA_NAME16']
    frm['area'] = frm['AREASQKM16']
    states = load_states()
    import get
    statesLookup = get.get_majority_area_lookup(frm, states)
    frm['STE_NAME16'] = [statesLookup[i] for i in frm.index]
    return frm

def load_aus():
    paths = [repoPath, 'resources', 'AUS_2016_AUST.shp']
    ausFrame = gpd.read_file(os.path.join(*paths))
    ausPoly = ausFrame.iloc[0]['geometry']
    return ausPoly

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
    frm['name'] = frm['SA{0}_NAME16'.format(str(level))]
    frm['area'] = frm['AREASQKM16']
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
    filename = "MB_2016_{0}.shp".format(state.upper())
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
def load_mb_all():
    states = {'vic', 'nsw', 'qld', 'nt', 'sa', 'act', 'wa', 'tas'}
    return pd.concat([load_mb(state) for state in states])

def load_lga_pop():
    filePath = os.path.join(repoPath, 'resources', 'LGA ERP GeoPackage 2018.gpkg')
    return gdf.from_file(filePath)

def load_sa2_pop():
    filePath = os.path.join(repoPath, 'resources', 'SA2 ERP GeoPackage 2018.gpkg')
    return gdf.from_file(filePath)

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

def load_gcc(gcc):
    global GCCNAMES
    return load_gccs().loc[GCCNAMES[gcc]]['geometry']

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
        region = region.buffer(np.sqrt(region.area) * 1e-4)
        geoms.append(region)
    frm = gdf(gccs, columns = ['gcc'], geometry = geoms)
    frm = frm.set_index('gcc')
    savePath = os.path.join(repoPath, 'resources', 'gcc.shp')
    frm.to_file(savePath)
    return frm

def load_region(region, fromLGAs = False):
    if fromLGAs:
        lgas = load_lgas(region)
        return shapely.ops.unary_union(lgas.convex_hull)
    else:
        global STATENAMES
        global GCCNAMES
        if region == 'aus':
            return load_aus()
        elif region in STATENAMES:
            return load_state(region)
        elif region in GCCNAMES:
            return load_gcc(region)
        else:
            raise ValueError

def load_region_quadkeys(region, zoom):
    poly = load_region(region)
    return load_poly_quadkeys(poly, zoom)
def load_poly_quadkeys(poly, zoom):
    import hashlib
    s = str(poly).encode()
    polyHash = \
        str(int(hashlib.sha256(s).hexdigest(), 16) % (10 ** 8))
    filename = \
        'poly' \
        + '_' + polyHash \
        + '_' + str(zoom) \
        + '_' + 'quadkeys' \
        + '.json'
    filePath = os.path.join(repoPath, 'resources', filename)
    if os.path.isfile(filePath):
        with open(filePath, 'r') as f:
            quadkeys = json.load(f)
    else:
        quadkeys = utils.find_quadkeys(
            poly,
            zoom,
            easy = False,
            soft = True
            )
        with open(filePath, 'w') as f:
            json.dump(quadkeys, f)
    return quadkeys

# #     allFilePath = os.path.join(dataDir, subDir, 'all.shp')
#     allFilePath = os.path.join(dataDir, subDir, '_all.csv')
#     if os.path.isfile(allFilePath):
# #         loaded = gdf.from_file(allFilePath)
#         loaded = pd.read_csv(allFilePath)
#         fix_dates = lambda t: pd.Timestamp(datetime.strptime(
#             t.replace(':', ''),
#             '%Y-%m-%d %H%M%S%z'
#             ))
#         fixedDates = {t: fix_dates(t) for t in set(loaded['datetime'])}
#         loaded['datetime'] = loaded['datetime'].apply(lambda t: fixedDates[t])
#         loaded['datetime'] = loaded['datetime'].dt.tz_convert(TZS[state])
#         alreadyKeys = set([standardise_timestamp(t) for t in fixedDates.values()])
# #         timestamps = set(loaded.reset_index()['datetime'])
# #         alreadKeys = set([standardise_timestamp(t) for t in timestamps])
#         loaded['quadkey'] = loaded['quadkey'].astype(str)
#         if dataset == 'mob':
#             loaded['end_key'] = loaded['end_key'].astype(str)
#             loaded = loaded.set_index(['datetime', 'quadkey', 'end_key'])
#         else:
#             loaded = loaded.set_index(['datetime', 'quadkey'])
#     else:
#         loaded = None
#         alreadyKeys = set()

# if region == 'Greater Melbourne':
#     # buffer to include Geelong/Bellarine
#     lgas = clip_to_gcc(lgas, gcc, buffer = 0.3)
#     lgas = lgas.drop(21450) # drop Cardinia
#     lgas = lgas.drop(24130) # drop Macedon Ranges

#     el
#         if region in STATENAMES:
#             lgas = lgas.loc[lgas['STE_NAME16'] == STATENAMES[region]]
#             if region == 'nsw':
#                 lgas = lgas.drop(19399) # drop Unincorporated
#         elif region in GCCNAMES:
#             from processing import clip_to_gcc
#             if region == 'mel':
#                 # buffer to include Geelong/Bellarine
#                 lgas = clip_to_gcc(lgas, GCCNAMES[region], buffer = 0.3)
#                 lgas = lgas.drop(21450) # drop Cardinia
#                 lgas = lgas.drop(24130) # drop Macedon Ranges
#             elif region == 'syd':
#                 lgas = clip_to_gcc(lgas, GCCNAMES[region], **kwargs)
#                 lgas = lgas.drop(10900) # drop Blue Mountains
#                 lgas = lgas.drop(13800) # drop Hawkesbury
#                 lgas = lgas.drop(11650) # drop Central Coast
#             else:
#                 lgas = clip_to_gcc(lgas, GCCNAMES[region])
#         else:
#             raise KeyError
#         if keep:
#             raise Exception("Not supported yet.")
#             remLabel = 'OutOfBounds'
#             remKeys = set(allLGAs.index).difference(set(lgas.index))
#             remGeoms = list(allLGAs.loc[remKeys]['geometry'])
#             remGeom = utils.mixed_polys_to_multi(remGeoms)
#             remData = {k: [remLabel] for k in lgas.columns}
#             lgas = lgas.append(gdf(
#                 remData, geometry = [remGeom,], index = [remLabel]
#                 ))
#         lgas = lgas.drop(['STE_NAME16', 'STE_CODE16'], axis = 1)
#     return lgas