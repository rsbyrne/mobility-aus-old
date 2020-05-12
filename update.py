import os

import produce

repoPath = os.path.abspath(os.path.dirname(__file__))
productsDir = os.path.join(repoPath, 'products')
transientDir = os.path.join(repoPath, 'transient')

regions = {'vic', 'mel', 'syd', 'nsw'}

for region in regions:
    frm, frmGDF = produce.make_mob_lga_date(
        region,
        get = True,
        return_both = True
        )
    frm.to_csv(
        os.path.join(productsDir, region + '.csv')
        )
    frmGDF.to_file(
        os.path.join(transientDir, region + '.geojson'),
        driver = 'GeoJSON'
        )
