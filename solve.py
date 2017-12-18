from imposm.parser import OSMParser
from collections import defaultdict
from math import sqrt
import networkx as nx
import sys
from postman_problems import graph
import itertools

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


class Postman(object):
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
        return min_edge

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

    def create_graph(self, required):
        graph = nx.MultiGraph()
        for i, edge in enumerate(self.edges):
            osmid, from_node, to_node, from_coords, to_coords, d = edge
            req = tuple(sorted((from_node, to_node))) in required
            graph.add_edge(from_node, to_node, id=i, required=req, distance=d)
        return graph

    def augment_graph(self, g_full):
        g_req = graph.create_required_graph(g_full)
        odd_nodes = graph.get_odd_nodes(g_req)
        odd_node_pairs = list(itertools.combinations(odd_nodes, 2))
        odd_node_pairs_shortest_paths = graph.get_shortest_paths_distances(g_full,
                                                                           odd_node_pairs,
                                                                           'distance')
        g_odd_complete = graph.create_complete_graph(odd_node_pairs_shortest_paths, flip_weights=True)
        odd_matching = graph.dedupe_matching(nx.algorithms.max_weight_matching(g_odd_complete, True))
        g_aug = graph.add_augmenting_path_to_graph(g_req, odd_matching)
        return g_aug, g_req

    def solve_brooks(self, required):
        g_full = self.create_graph(required)
        g_req = graph.create_required_graph(g_full)
        graph.assert_graph_is_connected(g_req)
        odd_nodes = graph.get_odd_nodes(g_req)
        odd_node_pairs = list(itertools.combinations(odd_nodes, 2))
        odd_node_pairs_shortest_paths = graph.get_shortest_paths_distances(g_full,
                                                                           odd_node_pairs,
                                                                           'distance')
        g_odd_complete = graph.create_complete_graph(odd_node_pairs_shortest_paths, flip_weights=True)
        odd_matching = graph.dedupe_matching(nx.algorithms.max_weight_matching(g_odd_complete, True))
        g_aug = graph.add_augmenting_path_to_graph(g_req, odd_matching)

        start_node = next(iter(required))[0]
        circuit = list(graph.create_eulerian_circuit(g_aug, g_full, start_node))

        return circuit

    def solve_c42(self, required):
        """Solve using fredrickson's heuristic"""
        g_full = self.create_graph(required)
        g_req = graph.create_required_graph(g_full)
        node_pairs = list(itertools.combinations(g_req, 2))
        g_aug = g_full.copy()
        # Add edges
        for i, pair in enumerate(node_pairs):
            try:
                d = nx.dijkstra_path_length(g_full, pair[0], pair[1], weight='distance')
                # Only setting distance now, not id.
                # Do we need these attributes later on?
                g_aug.add_edge(pair[0], pair[1], distance=d, id=-i, required=False)
            except:
                pass
        for edge in g_aug.edges():
            # remove duplicate edges
            data = g_aug[edge[0]][edge[1]]
            if len(data) > 1:
                deletions = set()
                for pair in itertools.combinations(data.keys(), 2):
                    key1, key2 = pair
                    if data[key1]['distance'] - data[key2]['distance'] < 1e-09 \
                            and not data[key2]['required']:
                        #g_aug.remove_edge(edge[0], edge[1], key2)
                        deletions.add(key2)
                for key in deletions:
                    g_aug.remove_edge(edge[0], edge[1], key)

            # loop through the rest and remove edges that have a duplicate length in combination
            deletions = set()
            for node in g_aug[edge[0]]:
                if edge[1] in g_aug[node]:
                    # Now loop through all parallel edges and remove duplicates
                    print g_aug[edge[0]][node]
                    print g_aug[node][edge[1]]
                    if g_aug[edge[0]][node][0]['distance'] - g_aug[node][edge[1]][0]['distance'] < 1e-09 \
                            and not g_aug[edge[0]][edge[1]][0]['required']:
                        #g_aug.remove_edge(edge[0], edge[1], 0)
                        print "delete the edge"
                        deletions.add(edge)
                        break
            for edge in deletions:
                g_aug.remove_edge(edge[0], edge[1])

            required = g_aug.get_edge_data(edge[0], edge[1], 'required')
            if not required:
                distance = g_aug.get_edge_data(edge[0], edge[1], 'distance')
        # Remove edges (can we really do this? We are using floats here).

        raise Exception
        node_pairs_shortest_paths = graph.get_shortest_paths_distances(g_full,
                                                                       node_pairs,
                                                                       'distance')

        print node_pairs_shortest_paths
        T = nx.minimum_spanning_tree(g_bar, 'distance')


        start_node = next(iter(required))[0]


if __name__ == '__main__':
    import re
    pattern = re.compile(r'(\d{4}\w{2})(.*)')
    postman = Postman('map.osm')
    required = set()
    for arg in sys.argv[1:]:
        m = pattern.match(arg)
        if m:
            postcode, number = m.groups()
            edge = postman.find_edge_by_address(postcode, number)
            if edge:
                 required.add(tuple(sorted((edge[1], edge[2]))))
            else:
                print "arg {} not found".format(arg)
        else:
            print "invalid postcode ()".format(arg)
    print required
    print postman.solve_c42(required)
