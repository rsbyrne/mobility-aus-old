import numpy as np
import pandas as pd
df = pd.DataFrame
import geopandas as gpd
gdf = gpd.GeoDataFrame

import load
import utils
import processing
from processing import aggregate_mob_tiles_to_regions

def make_mob_lga_date(
        region,
        get = False,
        as_gdf = False,
        return_both = False
        ):

    if get:
        raw = load.get_fb_mob_tiles(region)
    else:
        raw = load.load_fb_mob_tiles(region)

    frm = raw
    frm = processing.aggregate_mob_tiles_to_lga(frm, region)
    frm = processing.aggregate_by_date(frm)
    procFrm = frm

    frm = procFrm
    frm = frm.reset_index()
    frm = df(frm.groupby(['date', 'start'])['n'].aggregate(sum))
    totalsFrm = frm

    frm = procFrm
    frm = frm.reset_index()
    frm = frm.loc[frm['length_km'] <= 0.]
    frm = df(frm.groupby(['date', 'start'])['n'].aggregate(sum))
    immobFrm = frm

    assert(immobFrm['n'].sum() / totalsFrm['n'].sum() < 1.)
    frm = immobFrm / totalsFrm * 100.
    frm = frm.reset_index()
    frm = frm.rename({'start': 'LGA', 'n': '%stay'}, axis = 1)
    frm = frm.set_index(['date', 'LGA'])
    ratioFrm = frm

    runningAvs = ratioFrm.reset_index().groupby('LGA').aggregate(np.mean)
    frm = ratioFrm.copy()
    frm = frm.reset_index().set_index('LGA')
    frm['rAv'] = runningAvs.loc[frm.index]
    frm['%anom'] = (frm['%stay'] / frm['rAv'] - 1.) * 100.
    frm = frm.drop('rAv', axis = 1)
    anomFrm = frm

    frm = anomFrm
    lgas = load.load_lgas()
    if as_gdf or return_both:
        geometry = list(frm.reset_index()['LGA'].apply(
            lambda x: lgas.loc[x]['geometry']
            ))
        frmGDF = gdf(frm.copy(), geometry = geometry)
        if return_both:
            return frm, frmGDF
        else:
            return frmGDF
    return frm