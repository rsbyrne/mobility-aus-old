from itertools import product
import numpy as np
import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame
import shapely
import load
from aggregate import aggregate
from utils import quadkey_to_poly, quadkeys_to_polys

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

import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame
sjoin = gpd.tools.sjoin
import numpy as np
import load

def get_intersections(fromFrm, toFrm):
    joined = gpd.tools.sjoin(fromFrm, toFrm, 'left', 'intersects')
    groupby = joined['index_right'].groupby(joined.index)
    def agg_func(s):
        nonlocal fromFrm
        nonlocal toFrm
        toIndices = sorted(set(s))
        if len(toIndices) == 1:
            return [(toIndices[0], 1)]
        toPolys = [toFrm.loc[i]['geometry'] for i in toIndices]
        fromIndex = s.index[0]
        fromPoly = fromFrm.loc[fromIndex]['geometry']
        weights = [fromPoly.intersection(p).area for p in toPolys]
        weights = [w / sum(weights) for w in weights]
        return list(zip(toIndices, weights))
    return groupby.aggregate(agg_func)

def get_quadFrm(frm):
    flatFrm = frm.reset_index()
    quadkeys = sorted(set(flatFrm['quadkey']))
    if 'end_key' in flatFrm:
        quadkeys = sorted(set([*quadkeys, *flatFrm['end_key']]))
    quadpolys = quadkeys_to_polys(quadkeys)
    quadFrm = gdf(geometry = quadpolys, index = quadkeys)
    quadFrm.index.name = 'quadkey'
    return quadFrm

def aggregate_mob_tiles_to_regions(fromFrm, toFrm, key = 'n'):
    quadFrm = get_quadFrm(fromFrm)
    weights = get_intersections(quadFrm, toFrm)
    def disagg_func(inp):
        nonlocal weights
        grDF = inp[1]
        date = grDF.iloc[0]['datetime']
        startKey = grDF.iloc[0]['quadkey']
        endKeys, ns = [*zip(*[*grDF[['end_key', key]].values])]
        startWeights = weights.loc[startKey]
        outRows = []
        for endKey, n in zip(endKeys, ns):
            endWeights = weights.loc[endKey]
            possibleJourneys = list(product(startWeights, endWeights))
            for pair in possibleJourneys:
                (start, startWeight), (end, endWeight) = pair
                outRow = [start, end, n * startWeight * endWeight]
                outRow.append(date)
                outRows.append(outRow)
        return outRows
    groupby = fromFrm.reset_index().groupby(['datetime', 'quadkey'])
    groupby = groupby[['datetime', 'quadkey', 'end_key', key]]
    out = [i for sl in [disagg_func(f) for f in groupby] for i in sl]
    outFrm = df(out, columns = ['start', 'end', key, 'datetime'])
    outFrm = df(outFrm.groupby(['start', 'end', 'datetime'])[key].aggregate(np.sum))
    return outFrm

def aggregate_mob_tiles_to_lga(fromFrm):
    lgas = load.load_lgas()
    return aggregate_mob_tiles_to_regions(fromFrm, lgas)

def aggregate_mob_tiles_lga_date(fromFrm):
    return aggregate_by_date(aggregate_mob_tiles_to_lga(fromFrm))

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
    if not type(aggregate) in {set, list, tuple}:
        aggregate = [aggregate]
    indexNames = [nm for nm in frm.index.names if not nm == datetimeKey]
    frm = frm.copy()
    frm['date'] = list(frm.reset_index()[datetimeKey].apply(make_date))
    frm = frm[[*aggregate, 'date']].reset_index()
    groupby = frm.groupby(['date', *indexNames])
    frm = groupby.aggregate(func)
    return frm