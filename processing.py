from itertools import product
import os
import json
import numpy as np
import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame
sjoin = gpd.tools.sjoin
import shapely
import load
from aggregate import aggregate
from utils import quadkey_to_poly, quadkeys_to_polys

repoPath = os.path.abspath(os.path.dirname(__file__))

def quadkeys_to_lgas(quadkeys, skipkeys = set()):
    quadkeys = sorted(set([q for q in quadkeys if not q in skipkeys]))
    fromPolys = [quadkey_to_poly(q) for q in quadkeys]
    lgaFrame = load.load_lgas()
    toPolys, toLGAs = zip(*[
        (g, lga)
        for g, lga in zip(
                list(lgaFrame['geometry']),
                list(lgaFrame.index)
                ) \
            if not g is None
        ])
    matches = aggregate(fromPolys, toPolys)
    return dict(zip(quadkeys, [toLGAs[m] for m in matches]))

def get_intersections(fromFrm, toFrm):
    return make_intersections(fromFrm, toFrm)
def make_intersections(fromFrm, toFrm):
    joined = gpd.tools.sjoin(fromFrm, toFrm, 'left', 'intersects')
    joined = joined.dropna()
    groupby = joined['index_right'].groupby(joined.index)
    def agg_func(s):
        nonlocal fromFrm
        nonlocal toFrm
        toIndices = sorted(set([int(x) for x in s]))
        if len(toIndices) == 1:
            return [(toIndices[0], 1)]
        toPolys = [toFrm.loc[i]['geometry'] for i in toIndices]
        fromIndex = s.index[0]
        fromPoly = fromFrm.loc[fromIndex]['geometry']
        weights = [fromPoly.intersection(p).area for p in toPolys]
        weights = [w / sum(weights) for w in weights]
        return list(zip(toIndices, weights))
    weights = groupby.aggregate(agg_func)
    weights = dict(zip(weights.index, list(weights)))
    return weights

def get_quadFrm(frm):
    flatFrm = frm.reset_index()
    quadkeys = sorted(set(flatFrm['quadkey']))
    if 'end_key' in flatFrm:
        quadkeys = sorted(set([*quadkeys, *flatFrm['end_key']]))
    quadpolys = quadkeys_to_polys(quadkeys)
    quadFrm = gdf(geometry = quadpolys, index = quadkeys)
    quadFrm.index.name = 'quadkey'
    return quadFrm

def get_quadkey_lga_weights(poly, zoom, **kwargs):
    print("Getting weights...")
    import hashlib
    s = str(poly).encode()
    polyHash = \
        str(int(hashlib.sha256(s).hexdigest(), 16) % (10 ** 8))
    filename = \
        'poly' \
        + '_' + polyHash \
        + '_' + str(zoom) \
        + '_' + 'weights' \
        + '.json'
    filePath = os.path.join(repoPath, 'resources', filename)
    if not os.path.isfile(filePath):
        weights = make_quadkey_lga_weights(poly, zoom, **kwargs)
        with open(filePath, 'w') as f:
            json.dump(weights, f)
    else:
        with open(filePath, 'r') as f:
            weights = json.load(f)
    print("Weights obtained.")
    return weights
def make_quadkey_lga_weights(poly, zoom, lgas = None):
    if lgas is None:
        lgas = load.load_lgas()
    quadkeys = load.load_poly_quadkeys(poly, zoom)
    quadFrm = get_quadFrm(df(quadkeys, columns = ['quadkey']))
    weights = get_intersections(quadFrm, lgas)
    return weights

def aggregate_mob_tiles_to_regions(
        fromFrm,
        toFrm = None,
        weights = None,
        key = 'n'
        ):
    assert not (toFrm is None and weights is None)
    if weights is None:
        print("Getting weights...")
        quadFrm = get_quadFrm(fromFrm)
        weights = get_intersections(quadFrm, toFrm)
        print("Weights obtained.")
    print("Aggregating to regions...")
    fromFrm = fromFrm.reset_index().set_index('quadkey')
    fromFrm = fromFrm.drop(
        set(fromFrm.index).difference(set(weights.keys()))
        )
    fromFrm = fromFrm.reset_index().set_index('end_key')
    fromFrm = fromFrm.drop(
        set(fromFrm.index).difference(set(weights.keys()))
        )
    fromFrm = fromFrm.reset_index().set_index(
        ['datetime', 'quadkey', 'end_key']
        )
    def disagg_func(inp):
        nonlocal weights
        grDF = inp[1]
        date = grDF.iloc[0]['datetime']
        startKey = grDF.iloc[0]['quadkey']
        endKeys, length_kms, ns = [
            *zip(*[*grDF[['end_key', 'length_km', key]].values])
            ]
        startWeights = weights[startKey]
        outRows = []
        for endKey, length_km, n in zip(endKeys, length_kms, ns):
            endWeights = weights[endKey]
            possibleJourneys = list(product(startWeights, endWeights))
            for pair in possibleJourneys:
                (start, startWeight), (end, endWeight) = pair
                outRow = [start, end, length_km, n * startWeight * endWeight]
                outRow.append(date)
                outRows.append(outRow)
        return outRows
    groupby = fromFrm.reset_index().groupby(['datetime', 'quadkey'])
    groupby = groupby[['datetime', 'quadkey', 'end_key', 'length_km', key]]
    out = [i for sl in [disagg_func(f) for f in groupby] for i in sl]
    outFrm = df(out, columns = ['start', 'end', 'length_km', key, 'datetime'])
    outFrm = df(
        outFrm.groupby(
            [k for k in outFrm.columns if not k == key]
            )[key].aggregate(np.sum))
    outFrm = outFrm.reset_index()
    print("Aggregated.")
    return outFrm

def aggregate_pop_tiles_to_regions(
        fromFrm,
        toFrm = None,
        weights = None,
        key = 'n'
        ):
    assert not (toFrm is None and weights is None)
    if weights is None:
        print("Getting weights...")
        quadFrm = get_quadFrm(fromFrm)
        weights = get_intersections(quadFrm, toFrm)
        print("Weights obtained.")
    print("Aggregating to regions...")
    fromFrm = fromFrm.reset_index().set_index('quadkey')
    fromFrm = fromFrm.drop(
        set(fromFrm.index).difference(set(weights.keys()))
        )
    fromFrm = fromFrm.reset_index().set_index(
        ['datetime', 'quadkey']
        )
    def disagg_func(inp):
        nonlocal weights
        grDF = inp[1]
        date = grDF.iloc[0]['datetime']
        n = float(grDF[key])
        startKey = grDF.iloc[0]['quadkey']
        startWeights = weights[startKey]
        outRows = []
        for start, startWeight in startWeights:
            outRow = [start, n * startWeight]
            outRow.append(date)
            outRows.append(outRow)
        return outRows
    groupby = fromFrm.reset_index().groupby(['datetime', 'quadkey'])
    groupby = groupby[['datetime', 'quadkey', key]]
    out = [i for sl in [disagg_func(f) for f in groupby] for i in sl]
    outFrm = df(out, columns = ['start', key, 'datetime'])
    outFrm = df(
        outFrm.groupby(
            ['start', 'datetime']
            )[key].aggregate(np.sum))
    print("Aggregated.")
    return outFrm

def aggregate_tiles_to_lga(frm, region, lgas = None, variant = 'mob'):
    if lgas is None:
        lgas = load.load_lgas()
    zoom = list(set([
        len(str(qk)) for qk in frm.reset_index()['quadkey']
        ]))[0]
    poly = load.load_region(region, fromLGAs = True)
    weights = get_quadkey_lga_weights(
        poly,
        zoom,
        lgas = lgas
        )
    if variant == 'mob':
        return aggregate_mob_tiles_to_regions(frm, weights = weights)
    elif variant == 'pop':
        return aggregate_pop_tiles_to_regions(frm, weights = weights)
    else:
        raise ValueError
def aggregate_pop_tiles_to_lga(frm, region, lgas = None):
    return aggregate_tiles_to_lga(frm, region, lgas, 'pop')
def aggregate_mob_tiles_to_lga(frm, region, lgas = None):
    return aggregate_tiles_to_lga(frm, region, lgas, 'mob')

def clip_to_gcc(frm, gcc, convex = True, **kwargs):
    poly = load.load_gccs().loc[gcc]['geometry']
    if convex:
        poly = poly.convex_hull
    frm = clip_frm(frm, poly, **kwargs)
    return frm
def unify_frm(frm, convex = True):
    if convex:
        frm = frm.convex_hull
    poly = shapely.ops.unary_union(frm)
    return poly
def clip_frm(frm, poly, op = 'within', buffer = 1e-3, **kwargs):
    if type(poly) is gdf:
        poly = unify_frm(poly, **kwargs)
    if not buffer is None:
        poly = poly.buffer(np.sqrt(poly.area) * buffer)
    func = getattr(frm['geometry'], op)
    return frm.loc[func(poly)]

def fill_regions(frmA, frmB, vals = None, clip = True):
    if clip:
        frmB = clip_frm(frmB, frmA, op = 'intersects')
    indices, polys = frmB.index, frmB['geometry']
    if vals is None:
        vals = {k: None for k in frmA.columns}
    for c, p in zip(indices, polys):
        if not c in frmA.index:
            series = pd.Series({'geometry': p, **vals})
            series.name = c
            frmA = frmA.append(series)
    return frmA

def make_date(d):
    return '-'.join([str(x).zfill(2) for x in d.timetuple()[:3]])
def aggregate_by_date(
        frm,
        aggregate = 'n',
        datetimeKey = 'datetime',
        func = np.sum
        ):
    print("Aggregating by date...")
    if not type(aggregate) in {set, list, tuple}:
        aggregate = [aggregate]
    indexNames = [nm for nm in frm.index.names if not nm == datetimeKey]
    frm = frm.copy()
    frm['date'] = list(frm.reset_index()[datetimeKey].apply(make_date))
    frm['date'] = pd.to_datetime(frm['date']).dt.date
    frm = frm[[*aggregate, 'date']].reset_index()
    groupby = frm.groupby(['date', *indexNames])
    frm = groupby.aggregate(func)
    print("Aggregated.")
    return frm