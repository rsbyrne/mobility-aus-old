import os

import produce

repoPath = os.path.abspath(__file__)
productsDir = os.path.join(repoPath, 'products')
transientDir = os.path.join(repoPath, 'transient')

regions = {'vic', 'mel', 'syd', 'nsw'}

for region in regions:
    frm, frmGDF = produce.make_mob(
        region,
        get = True,
        as_gdf = True,
        return_both = True
        )
    frm.to_csv(
        os.path.join(productsDir, state + '.csv')
        )
    frmGDF.to_file(
        os.path.join(transientDir, state + '.geojson'),
        driver = 'GeoJSON'
        )
