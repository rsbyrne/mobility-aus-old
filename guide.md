---
layout: page
title: guide
---

# Guide

## Intro

The data provided through this portal are anonymised aggregations of user mobility data
sourced through the Facebook Data For Good program.
The data have been heavily processed by both ourselves and Facebook to protect privacy and
intellectual property while providing the best possible utility.

## Overview

The data we provide are mobility records of thousands of Facebook users for several Australian states and cities
going as far back as the beginning of April. The data are aggregated by date and local government area.
We provide the raw data as well as some basic summary plots and maps.

The columns of the provided data are as labelled:
- *date*: The local date.
- *LGA*: The Australian Bureau of Statistics
[code](https://www.abs.gov.au/ausstats/abs@.nsf/Lookup/by%20Subject/1270.0.55.003~July%202019~Main%20Features~Local%20Government%20Areas%20(LGAs)~2)
for the local government area in question.
- *stay*: The proportion of records for that date and LGA which show no movement
(i.e. the source and destination vicinities are the same).
- *km*: The average distance travelled per record for all records collected on that date and within that LGA.
- *weight*: The proportion of all records available for that day which registered a start position
somewhere inside the LGA.
- *visit*: Answers the question 'of the records that document travel between LGAs,
how many recorded destinations within this LGA?'

The maps show the 'km' dataset with colours mapped to the powers of ten,
i.e. '-3' represents metres, '-1' represents hundreds of metres, '1' represents tens of kilometres, *et cetera*.
The plots should be self-explanatory.

## Details

The data we provide are higher level aggregations of the orignal source data provided directly by Facebook.
These data are only shared with credentialed researchers and cannot be supplied in raw form.
We can however give some information about the shape of those data, and the approach taken
to aggregate them further for public release.

Facebook handles data requests by drawing bounding boxes over requested target regions.
The data is automatically aggregated to a level of geographic accuracy which is computationally tenable with respect
to the resources they have allocated to the task. The spatial resolution may be as little
as tens of metres or as many as hundreds. From the time the request is made, Facebook provides
thrice-daily updates of all user location data for trips which take place entirely
within the target region, including 'trips' of zero distance. Trips that cross the outer boundaries
are discarded.
(Note that only users who voluntarily activate location services are tracked in this manner;
we do not know how many users choose to do so, or what their demographics are,
but we are informed by Facebook that they compromise a small minority of all users.)

The final product is an ever-growing dataset which records, among other things:
1) The time and date of the observation, with three time bins per day in eight hour increments from midnight universal time.
Each bin is labelled with the start time of the bin, rather than the end time.
2) The [quadtile](https://docs.microsoft.com/en-us/bingmaps/articles/bing-maps-tile-system)
where that user was most frequently observerved during that time interval - i.e. the 'end' tile.
3) The quadtile where the user was most frequently observed during the previous eight-hour time window - i.e. the 'start' tile.

The records are supplied by Facebook aggregated by tile pair and time window: any set of start tile, end tile, and time bin
for which there are fewer than ten observed users are **discarded** to protect their privacy.

We are not permitted to share the data in this form, but we are encouraged to share data which has been processed
in some way. Our decision was to provide the data to the public aggregated by date and local government area.
This is done by performing a spatial join of the Facebook tile-based dataset with the ABS-provided LGA shapefile.
Tiles which lie across multiple LGAs are broken up and their data redistributed proportionally by area
across the intersecting LGAs. This yields a dataset of Facebook population 'n' keyed by
start LGA, stop LGA, datetime, and travel distance. Records whose starting LGA does not wholly lie within a ten percent buffer
of the original bounding box for the dataset as a whole are deemed intolerably incomplete and are discarded.
The remainder is then aggregated by region and day to produce the final data available through this portal.

## Tell me more

Users who wish for a more detailed account of the data processing methodology are welcome to peruse (and appropriate)
the source code for this project, which may be found in the associated [GitHub repository](github.com/rsbyrne/mobility-aus).
Users are also welcome to contact the project maintainer, [Rohan Byrne](mailto:rohan.byrne@unimelb.edu.au)
