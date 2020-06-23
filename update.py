import produce
from load import NoData

regions = {
    'vic', 'mel', 'nsw', 'syd', 'sa', 'ade',
    'wa', 'per', 'tas', 'qld', 'nt', 'aus',
    }
aggTypes = {
    'lga', 'sa2',
    }

absLookup = produce.get_abs_lookup(aggTypes, refresh = True)
for region in regions:
    for aggType in aggTypes:
        try:
            mob = produce.get_mob_date(
                region,
                aggType,
                get = False,
                refresh = True,
                override = False
                )
            produce.make_mob_plots(
                mob,
                region,
                aggType,
                )
            produce.make_mob_dateMap(
                mob,
                region,
                aggType,
                )
        except NoData:
            print("No data currently available for:", region)
