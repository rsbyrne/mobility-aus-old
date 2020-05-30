import produce
from load import NoData

regions = {
    'vic', 'mel',
    'nsw', 'syd',
    'sa', 'ade',
    'wa', 'per',
    'tas',
    'qld',
    'nt',
    'aus',
    }

for region in regions:
    try:
        mob = produce.get_mob_lga_date(region, get = False, refresh = True, override = False)
        produce.make_mob_plots(mob, region)
        produce.make_mob_lga_dateMap(mob, region)
    except NoData:
        print("No data currently available for:", region)
