# Crisis Mobility Data Portal

This repository has been established to provide free and easy access to aggregated mobility data products from Facebook and other sources. The data held here is authorised for general release to the public to support research activities related to the COVID-19 epidemic.

The site was established on the 12 May 2020 and will be updated at midnight daily for the foreseeable future.

Don't forget to [***read the guide***](https://rsbyrne.github.io/mobility-aus/guide) for these datas.

*CHANGES - 2 June 2020*

- Aggregations by Statistical Area have been added. Accordingly, the 'LGA' column has been renamed 'code'.
- The file *abs_lookup.csv* has been added to Products, providing a quick reference for ABS codes.

*CHANGES - 29 May 2020*

- Maps now allow selection of multiple datasets and have improved tooltips.
- The 'km' metric now ***excludes stay-at-home records***; please factor this in when refreshing your data.

*COMING SOON*

- [X] Data aggregation details
- [X] Interactive visualisations
- [X] Summary plots
- [X] Additional regions
- [X] Additional aggregations
- [ ] Improved summary plots
- [ ] Frequently Asked Questions
- [ ] Analysis spotlights

## Products

### Facebook Mobility by Local Government Area

These datas, sourced through the Facebook Data For Good program, provide various aggregated metrics
relating to mobility, including a measure of the 'stay-at-home ratio' during the COVID-19 crisis.
The areas in question are given by standard ABS LGA codes; the associated geometries may be freely sourced [here](https://www.abs.gov.au/ausstats/abs@.nsf/Lookup/by%20Subject/1270.0.55.003~July%202016~Main%20Features~Local%20Government%20Areas%20(LGA)~7).

**States**

[New South Wales](https://rsbyrne.github.io/mobility-aus/products/mob_lga_nsw.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_lga_nsw.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_lga_nsw.png))

[Victoria](https://rsbyrne.github.io/mobility-aus/products/mob_lga_vic.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_lga_vic.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_lga_vic.png))

[Queensland](https://rsbyrne.github.io/mobility-aus/products/mob_lga_qld.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_lga_qld.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_lga_qld.png))

[Western Australia](https://rsbyrne.github.io/mobility-aus/products/mob_lga_wa.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_lga_wa.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_lga_wa.png))

**Metros**

[Sydney](https://rsbyrne.github.io/mobility-aus/products/mob_lga_syd.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_lga_syd.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_lga_syd.png))

[Melbourne](https://rsbyrne.github.io/mobility-aus/products/mob_lga_mel.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_lga_mel.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_lga_mel.png))

[Adelaide](https://rsbyrne.github.io/mobility-aus/products/mob_lga_ade.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_lga_ade.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_lga_ade.png))

### Facebook Mobility by ABS Statistical Area (Level 2)

These datas area as above, but aggregated by ABS Statistical Areas (Level 2) rather than local councils.
Statistical Areas may be more convenient than councils for experienced researchers.
The areas in question are given by standard ABS SA2 codes; the associated geometries may be freely sourced [here](https://www.abs.gov.au/ausstats/abs@.nsf/Lookup/by%20Subject/1270.0.55.001~July%202016~Main%20Features~Statistical%20Area%20Level%202%20(SA2)~10014).

**States**

[New South Wales](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_nsw.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_nsw.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_nsw.png))

[Victoria](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_vic.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_vic.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_vic.png))

[Queensland](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_qld.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_qld.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_qld.png))

[Western Australia](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_wa.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_wa.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_wa.png))

**Metros**

[Sydney](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_syd.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_syd.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_syd.png))

[Melbourne](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_mel.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_mel.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_mel.png))

[Adelaide](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_ade.csv) ([maps](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_ade.html), [plots](https://rsbyrne.github.io/mobility-aus/products/mob_sa2_ade.png))

## Who are we?

This project has been launched under the auspices of a broad coalition of Australian scientists working on COVID-related problems. The first point of contact for any issues related to the product provided here is the project maintainer, Rohan Byrne: <rohan.byrne@unimelb.edu.au>
