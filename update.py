import sys
import os
parentDir = os.path.dirname(__file__)
if not parentDir in sys.path:
    sys.path.append(parentDir)
parentDir = os.path.dirname(parentDir)
if not parentDir in sys.path:
    sys.path.append(parentDir)

import produce

regions = {'vic', 'mel', 'syd', 'nsw', 'ade', 'sa', 'per', 'wa', 'tas', 'qld', 'nt'}
refresh = True

for region in regions:
    mob = produce.get_mob_lga_date(region, refresh = refresh)
    produce.make_mob_plots(mob, region)
    produce.make_mob_lga_dateMap(mob, region)