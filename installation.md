OSM python library needs protobuffer compiler.

Install the following ubuntu packages:

```
protobuf-compiler
libprotobuf-dev
libtokyocabinet-dev
```

Install the postgis database
I used instructions [here](https://www.digitalocean.com/community/tutorials/how-to-install-and-configure-postgis-on-ubuntu-14-04)
Roughly. I used stable packages. And named database postman.

Up to step 2
Skipped step 3

Convert OSM data to postgres as [here](http://wiki.openstreetmap.org/wiki/Osm2pgsql).
Installed ubuntu package
```
apt-get install osm2pgsql
```
