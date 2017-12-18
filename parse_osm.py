from imposm.parser import OSMParser
from collections import defaultdict
from math import sqrt
import sys

def dist_line(point, start, end):
    """Calculate the distance between `point`
       and the line defined by `start` and `end`"""
    x0, y0 = point
    x1, y1 = start
    x2, y2 = end

    return abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1) / \
           sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)

def dist(start, end):
    """Calculate the distance between `start` and `end`"""
    x1, y1 = start
    x2, y2 = end
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


class Osm(object):
    def __init__(self, filename):
        self.nodes = {}
        self.coords = {}
        self.ways = {}
        self.edges = []
        parser = OSMParser(concurrency=1,
                           ways_callback=self.ways_cb,
                           nodes_callback=self.nodes_cb,
                           coords_callback=self.coords_cb)
        parser.parse(filename)

        for osmid in self.ways:
            tags, refs = self.ways[osmid]
            # unpack the ways in to edges that will be used for the graphs later
            # we store the osm id of the way in the edge, but prolly not needed
            for i in xrange(len(refs) - 1):
                from_node, to_node = refs[i], refs[i+1]
                from_coords, _ = self.coords[from_node]
                to_coords, _ = self.coords[to_node]
                d = dist(from_coords, to_coords)
                # FIXME: make a class or namedtuple from edge
                self.edges.append((osmid, from_node, to_node,
                                   from_coords, to_coords, d))

    def find_closest_edge(self, point):
        #return min(self.edges, key=lambda e: dist_line(point, e[3], e[4]))
        min_value = float('Infinity')
        min_edge = None
        for e in self.edges:
            d = dist_line(point, e[3], e[4])
            if d < min_value:
                min_value = d
                min_edge = e
        return e

    def find_edge_by_address(self, postcode, number):
        for coords, tags in self.nodes.values():
            if tags:
                pass
            if tags \
                    and 'addr:postcode' in tags \
                    and tags['addr:postcode'] == postcode \
                    and 'addr:housenumber' in tags \
                    and tags['addr:housenumber'] == number:
                #print coords
                return self.find_closest_edge(coords)
        return None

    def nodes_cb(self, nodes):
        for osmid, tags, coords in nodes:
            self.nodes[osmid] = (coords, tags)

    def coords_cb(self, coords):
        for osmid, lon, lat in coords:
            self.coords[osmid] = ((lon, lat), {})

    def ways_cb(self, ways):
        for osmid, tags, refs in ways:
            self.ways[osmid] = tags, refs

if __name__ == '__main__':
    import re
    pattern = re.compile(r'(\d{4}\w{2})(.*)')
    osm = Osm('map.osm')
    required = []
    for arg in sys.argv[1:]:
        m = pattern.match(arg)
        if m:
            postcode, number = m.groups()
            edge = osm.find_edge_by_address(postcode, number)
            if edge:
                 required.append((edge[1], edge[2]))
            else:
                print "arg {} not found".format(arg)
    print required
