from imposm.parser import OSMParser
import sys
import os

class Extractor(object):
    def __init__(self, filename):
        parser = OSMParser(concurrency=1,
                           ways_callback=self.ways_cb,
                           nodes_callback=self.nodes_cb,
                           coords_callback=self.coords_cb)
        parser.parse(filename)


    def nodes_cb(self, nodes):
        for osmid, tags, coords in nodes:
            if tags \
                    and 'addr:postcode' in tags \
                    and 'addr:housenumber' in tags \
                    and 'addr:street' in tags:
                try:
                    print "{}{:<5} {}".format(tags['addr:postcode'],
                                              tags['addr:housenumber'],
                                              tags['addr:street'])
                except:
                    # Ignoring some unicode errors
                    pass
    def coords_cb(self, coords):
        pass

    def ways_cb(self, ways):
        pass

if __name__ == '__main__':
    import re
    Extractor(sys.argv[1])

