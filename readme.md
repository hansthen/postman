Introduction
-------------

This program will take a list of addresses and create a path
through all these addresses and display the result.

The program can be invoked using 
`python solve.py <postcode+housenumber>...`

The code uses the map-medium.osm map file. This is hard-coded. Other maps
will also work, but bigger maps take quite some time in solving.

I originally wanted to use postgis for the solution, so I spent some
time exporting the OSM database into postgis and getting to know the exported
format. This turned out to be a dead-end, as the postgis database did not
keep vertex identities with the edges, which is required for the algorithms
I was considering.

You can find my struggles with postgis in `postgis.md`.
