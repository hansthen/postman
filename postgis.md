You need to have followed the instructions in `installation.md` first.
Especially make sure you have created the postman database and enabled the postgis
extensions.

I added mappings for the street and postcode tags to make querying somewhat easier.

Import data

```
sudo -u postgres osm2pgsql --style postman.style --create --database postman map.osm
```

Run a few test queries

```
postman=# select name, highway from planet_osm_roads where highway is not NULL; 
            name             |  highway  
-----------------------------+-----------
 Vlaardingerdijk             | secondary
 Vlaardingerdijk             | secondary
 Burgemeester Van Haarenlaan | secondary
 Burgemeester Knappertlaan   | secondary
 Burgemeester Knappertlaan   | secondary
 Rubensplein                 | secondary
 Burgemeester Van Haarenlaan | secondary
 Burgemeester Van Haarenlaan | secondary
 Rubensplein                 | secondary
 Rubensplein                 | secondary
 Rubensplein                 | secondary
 Burgemeester Knappertlaan   | secondary
 Burgemeester Knappertlaan   | secondary
 Penninglaan                 | secondary
 Penninglaan                 | secondary
 Burgemeester Knappertlaan   | secondary
 Burgemeester Knappertlaan   | secondary
 Nieuwe Haven                | secondary
 Nieuwe Haven                | secondary
 Nieuwe Haven                | secondary
 Nieuwe Haven                | secondary
 Nieuwe Haven                | secondary
 Over de Vesten              | secondary
 Oranjebrug                  | secondary
 Oranjebrug                  | secondary
 Oranjebrug                  | secondary
 Oranjebrug                  | secondary
 Oranjestraat                | secondary
 Oranjestraat                | secondary
 Oranjebrug                  | secondary
 Oranjebrug                  | secondary
 Oranjestraat                | secondary
 Oranjestraat                | secondary
 Nieuwe Haven                | secondary
(34 rows)
```

Where I live:

```
postman=# select ST_AsText(ST_Transform(way,4326)) from planet_osm_point where "addr:postcode"='3117VD' and "addr:housenumber"='45';
               st_astext               
---------------------------------------
 POINT(4.383760350703 51.913217002198)
(1 row)
```

No idea what the 4326 is. Let's try.

```
postman=# select ST_AsText(ST_Transform(way,4327)) from planet_osm_point where "addr:postcode"='3117VD' and "addr:housenumber"='45';
ERROR:  GetProj4StringSPI: Cannot find SRID (4327) in spatial_ref_sys
postman=# select * from spatial_ref_sys;
```

Ah.

Now find the line segment closest to my home.

```
postman=# select osm_id, name, ST_Distance(ST_Transform(line.way,4326), (select ST_Transform(way,4326) from planet_osm_point where "addr:postcode"='3117VD' and "addr:housenumber"='45')) from planet_osm_line as line order by st_distance asc limit 1;
 osm_id  |     name      |     st_distance      
---------+---------------+----------------------
 7549914 | Rembrandtlaan | 9.41884164556252e-05
```

Cool, so we have a way to map addresses to edges.

Can we find special locations?
```
postman=# select "addr:housenumber", "addr:postcode" from planet_osm_point where shop is not NULL order by 2;
 addr:housenumber | addr:postcode 
------------------+---------------
 54               | 3111CH
 29               | 3111HB
 14               | 3111JK
 72b              | 3117 AT
 49               | 3117 CP
 77b              | 3117 CR
 56               | 3117 CT
 14               | 3117TK
 71c              | 3117VE
 6                | 
 110              | 
```
Oops, looks like we need to normalize the data.

So, gis import does not keep the vertices. That's a bugger.

Perhaps:
```
select osm_id, (select osm_id from planet_osm_point as point order by st_distance(st_transform(st_startpoint(line.way), 4326), st_transform(point.way, 4326)) asc limit 1) as from, (select osm_id from planet_osm_point as point order by st_distance(st_transform(st_endpoint(line.way), 4326), st_transform(point.way, 4326)) asc simit 1) as to from planet_osm_line as line;
```
But that does not look pretty.

