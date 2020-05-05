import os
import numpy as np
import itertools
import geopandas as gpd
gdf = gpd.GeoDataFrame
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import shapely

fileDir = os.path.abspath(os.path.dirname('__file__'))

with rasterio.open('fileDir/resources/apg16e_1_0_0.tif', 'r') as src:
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
frm = gdf(data, columns = ['pop'], crs = 'epsg:4326', geometry = geometry)

frm.to_file('fileDir/resources/aus_pop_16.shp')