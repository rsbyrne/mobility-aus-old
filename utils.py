import os
import numpy as np
from datetime import datetime, timezone
import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame
import shapely
from IPython.display import display
from load import load_datas
import mercantile

def _process_datetime(x):
    stripped = datetime.strptime(x, '%Y-%m-%d-%H%M')
    adjusted = stripped.astimezone(timezone.utc)
    return adjusted
def _process_geometry(x):
    return shapely.wkt.loads(x)

def centroid(x1, y1, x2, y2):
    return ((x1 + x2) / 2, (y1 + y2) / 2)
def quadkey_to_centroid(quadkey):
    return centroid(
        *mercantile.bounds(
            mercantile.quadkey_to_tile(str(quadkey))
            )
        )
def quadkey_to_point(quadkey):
    return shapely.geometry.Point(*quadkey_to_centroid(quadkey))
def quadkey_to_poly(quadkey):
    x0, y0, x1, y1 = mercantile.bounds(mercantile.quadkey_to_tile(str(quadkey)))
    poly = shapely.geometry.Polygon([[x0, y0], [x0, y1], [x1, y1], [x1, y0]])
    return poly
def point_to_polygon(point, zoom):
    tile = mercantile.tile(*np.array(point), zoom)
    quadkey = mercantile.quadkey(tile)
    poly = quadkey_to_poly(quadkey)
    return poly
def quadkey_to_lga(quadkey, lgas):
    point = quadkey_to_point(quadkey)
    matches = []
    for lga, polygon in zip(lgas.index, lgas['geometry']):
        if not polygon is None:
            if polygon.contains(point):
                matches.append(lga)
    if len(matches) == 0:
        lga = None
    elif len(matches) == 1:
        lga = matches[0]
    else:
        raise ValueError("Matched multiple geometries!")
    return lga
def get_quadkeys(totalBounds, zoom):
    allTiles = mercantile.tiles(*totalBounds, zoom)
    for tile in allTiles:
        yield int(mercantile.quadkey(tile))

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
        'n_crisis': lambda x: float(x) if not type(x) is str else 0.
        }
    procFuncs['geometry'] = lambda x: shapely.wkt.loads(x)
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

def load_population_tiles(
        dataDir,
        subDir,
        tz = None, # e.g. 'Australia/Melbourne'
        _trim = False
        ):
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
        'n_crisis': lambda x: float(x) if not type(x) is str else 0.
        }
    header, data = load_datas(
        os.path.join(dataDir, subDir),
        'csv',
        'datetime',
        _process_datetime,
        _printSuppress = True,
        **procFuncs
        )
    points = []
    filteredHeader = [key for key in header if not key in {'lon', 'lat'}]
    filtered = []
    for row in data:
        rowDict = dict(zip(header, row))
        point = shapely.geometry.Point(rowDict['lon'], rowDict['lat'])
        points.append(point)
        newrow = [rowDict[key] for key in filteredHeader]
        filtered.append(newrow)
    dataFrame = gdf(filtered, columns = filteredHeader, geometry = points)
    if not tz is None:
        dataFrame['datetime'].dt.tz_convert(tz)
    return dataFrame

def load_lgas(repoPath = '../..'):
    paths = [repoPath, 'resources', 'au_lga_shapefiles', 'LGA_2019_AUST.shp']
    lgaShapes = gpd.read_file(os.path.join(*paths))
    lgaShapes['LGA_CODE19'] = lgaShapes['LGA_CODE19'].astype(int)
    lgaShapes['STE_CODE16'] = lgaShapes['STE_CODE16'].astype(int)
    lgaLookup = lgaShapes.set_index('LGA_CODE19')
    return lgaLookup

def load_pbs(repoPath = '../..'):
    paths = [repoPath, 'resources', 'pb_lga_combined', 'pb_lga_combined.shp']
    pbShapes = gpd.read_file(os.path.join(*paths))
    pbByPoly = pbShapes.set_index('polygon_id')
    return pbByPoly

# def process_fb_mobility(mobilityData, pbs, lgas):
#     commonPolys = pbs.loc[mobilityData['Starting Location']]
#     lgaCol = list(commonPolys['LGA_CODE19'])
#     mobilityData['LGA_CODE19'] = lgaCol

# filternulls = pd.to_numeric(vicPopTiles['n_crisis'], errors = 'coerce').notnull()
# vicPopTiles = vicPopTiles[filternulls]

# data = data.replace('\\N', 0.)