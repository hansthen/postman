Introduction
-------------

This program will take a list of addresses and create a path
through all these addresses and display the result. The program
uses Frederickson's heuristic to approximate the shortest path.

The program can be invoked using 
````
python solve.py <postcode+housenumber>...
```

The code uses the map-medium.osm map file. This is hard-coded. Other maps
will also work, but bigger maps take quite some time in solving.

I originally wanted to use postgis for the solution, so I spent some
time exporting the OSM database into postgis and getting to know the exported
format. This turned out to be a dead-end, as the postgis database did not
keep vertex identities with the edges, which is required for the algorithms
I was considering.

You can find my struggles with postgis in `postgis.md`.

Notes for testing
-----------------

To create a list of valid addresses in a map use
```
python addresses.py <osm.map-file> > test-set 
```

To test against 20 random addresses do and do a visual inspection of the route.
```
sort -R test-set | head -n 20 | awk -F\  '{print $1} | xargs python solve.py'
```

Known bugs and limitations
--------------------------
1. Command line arguments are severly limited. I'd like to use argparse to make
map and several output options configurable as well as the name of the input map
and the solver used.

2. The resulting route is plotted, but not displayed in order. It'd be nice if Jane
had actual instructtions.

3. There is a bug in my implementation of Fredrickson's algorithm. It leaves gaps in the
circuit. I have manually fixed those gaps for now, but that is a stopgap solution. The
vertices that have this problem are marked blue (difficult to see but you can enlarge 
the graph.) At first glance it looks like it misses edges that require walking back over
a (required?) edge in the opposite direction.
