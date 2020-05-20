import produce

#regions = {'vic', 'mel', 'syd', 'nsw', 'ade', 'sa', 'per', 'wa', 'tas', 'qld', 'nt'}
regions = {'vic', 'mel', 'nsw', 'syd'}
refresh = True
get = False

for region in regions:
    mob = produce.get_mob_lga_date(region, refresh = refresh, get = get)
    produce.make_mob_plots(mob, region)
    produce.make_mob_lga_dateMap(mob, region)
