import os
import numpy as np
from datetime import datetime, timezone
import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame
from IPython.display import display
import shapely
import mercantile

def quadkey_to_poly(quadkey, flip = (False, False)):
    x0, y0, x1, y1 = mercantile.bounds(mercantile.quadkey_to_tile(quadkey))
    if flip[0]:
        x0, x1 = -x0, -x1
    if flip[1]:
        y0, y1 = -y0, -y1
    poly = shapely.geometry.Polygon([[x0, y0], [x0, y1], [x1, y1], [x1, y0]])
    return poly
def quadkeys_to_polys(quadkeys):
    quadDict = {q: quadkey_to_poly(q) for q in sorted(set(quadkeys))}
    return [quadDict[q] for q in quadkeys]

def centroid(x1, y1, x2, y2):
    return ((x1 + x2) / 2, (y1 + y2) / 2)
def quadkey_to_centroid(quadkey):
    return centroid(
        *mercantile.bounds(
            mercantile.quadkey_to_tile(quadkey)
            )
        )
def quadkey_to_point(quadkey):
    return shapely.geometry.Point(*quadkey_to_centroid(quadkey))
def quadkey_to_poly(quadkey):
    x0, y0, x1, y1 = mercantile.bounds(mercantile.quadkey_to_tile(quadkey))
    poly = shapely.geometry.Polygon([[x0, y0], [x0, y1], [x1, y1], [x1, y0]])
    return poly
def point_to_polygon(point, zoom):
    tile = mercantile.tile(*np.array(point), zoom)
    quadkey = mercantile.quadkey(tile)
    poly = quadkey_to_poly(quadkey)
    return poly
def get_quadkeys(totalBounds, zoom):
    allTiles = mercantile.tiles(*totalBounds, zoom)
    for tile in allTiles:
        yield mercantile.quadkey(tile)
def flip_quadkey(q, flip):
    lng, lat = quadkey_to_centroid(q)
    z = len(q)
    if flip[0]: lng = -lng
    if flip[1]: lat = -lat
    tile = mercantile.tile(lng, lat, z)
    return mercantile.quadkey(tile)

def children(quadkeys, levels = 1):
    if not type(quadkeys) is list:
        quadkeys = [quadkeys,]
    for level in range(levels):
        childrenKeys = []
        for qk in quadkeys:
            childrenKeys.extend([
                mercantile.quadkey(t) \
                    for t in mercantile.children(mercantile.quadkey_to_tile(qk))
                ])
        quadkeys = childrenKeys
    return quadkeys

def find_quadkeys(poly, zoom, easy = False, soft = True):
    z = 1
    outKeys = []
    quadkeys = ['0', '1', '2', '3']
    nChecks = 0
    convexPoly = poly.convex_hull.buffer(
        np.sqrt(poly.area) * 1e-3
        )
    squarePoly = convexPoly.envelope
    if easy:
        toPoly = convexPoly
    else:
        toPoly = poly
    while z <= zoom:
        quadpolys = [quadkey_to_poly(q) for q in quadkeys]
        certain = []
        if z < zoom:
            check = []
        for q, qp in zip(quadkeys, quadpolys):
            if qp.intersects(squarePoly):
                if qp.within(toPoly):
                    certain.append(q) 
                elif qp.intersects(toPoly):
                    check.append(q)
            nChecks += 1
        outKeys.extend(children(certain, zoom - z))
        if z < zoom:
            if len(check):
                quadkeys = children(check, 1)
        elif soft:
            outKeys.extend(check)
        z += 1
    print(nChecks)
    return outKeys

def standardise_timestamp(t):
    t = t.tz_convert('UTC')
    t = str(t)
    ts = t[:10] + '-' + t[11:13] + t[14:16]
    return ts
