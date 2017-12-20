from imposm.parser import OSMParser
from collections import defaultdict
from math import sqrt
import networkx as nx
import sys
from postman_problems import graph
import itertools
import matplotlib.pyplot as plt
import logging
import os

logging.basicConfig(level=os.getenv('C42_LOGLEVEL') or 'INFO')
logger = logging.getLogger(__name__)


def dist_line(point, start, end):
    """Calculate the distance between `point`
       and the line segment defined by `start` and `end`

       Shamelessly stolen from [here]("https://stackoverflow.com/questions/849211/shortest-distance-between-a-point-and-a-line-segment")
    """
    x0, y0 = point
    x1, y1 = start
    x2, y2 = end

    px = x2-x1
    py = y2-y1

    u =  ((x0 - x1) * px + (y0 - y1) * py) / (px**2 + py**2)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x0
    dy = y - y0

    return sqrt(dx**2 + dy**2)

def dist(start, end):
    """Calculate the distance between `start` and `end`"""
    x1, y1 = start
    x2, y2 = end
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


class Postman(object):
    def __init__(self, filename):
        self.nodes = {}
        self.coords = {}
        self.positions = {}
        self.ways = {}
        self.edges = []
        parser = OSMParser(concurrency=1,
                           ways_callback=self.ways_cb,
                           nodes_callback=self.nodes_cb,
                           coords_callback=self.coords_cb)
        parser.parse(filename)

        for osmid in self.ways:
            tags, refs = self.ways[osmid]
            if not 'highway' in tags:
                continue
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

    def nodes_cb(self, nodes):
        for osmid, tags, coords in nodes:
            self.nodes[osmid] = (coords, tags)
            if osmid in self.positions and self.positions[osmid] != coords:
                print "duplicate node", osmid, self.positions[osmid], coords
            else:
                self.positions[osmid] = coords

    def coords_cb(self, coords):
        for osmid, lon, lat in coords:
            self.coords[osmid] = ((lon, lat), {})
            if osmid in self.positions and self.positions[osmid] != (lon, lat):
                print "duplicate coords", osmid, self.positions[osmid], (lon, lat)
            else:
                self.positions[osmid] = (lon, lat)

    def ways_cb(self, ways):
        for osmid, tags, refs in ways:
            self.ways[osmid] = tags, refs

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

    def find_by_address(self, postcode, number):
        for item, (coords, tags) in self.nodes.items():
            if tags \
                    and 'addr:postcode' in tags \
                    and tags['addr:postcode'] == postcode \
                    and 'addr:housenumber' in tags \
                    and tags['addr:housenumber'] == number:
                return item, coords
        return None, None

    def find_edge_by_address(self, postcode, number):
        osmid, coords = self.find_by_address( postcode, number)
        if coords:
            return self.find_closest_edge(coords)
        return None

    def create_graph(self, required):
        graph = nx.MultiGraph()
        for i, edge in enumerate(self.edges):
            osmid, from_node, to_node, from_coords, to_coords, d = edge
            req = tuple(sorted((from_node, to_node))) in required
            graph.add_edge(from_node, to_node, id=i, required=req, distance=d)
        return graph

    def solve_brooks(self, required):
        """A reimplementation of andrew brooks' rpp solver

           using a different input format.
           This only works if the required edges are connected."""

        g_full = self.create_graph(required)
        g_req = graph.create_required_graph(g_full)
        graph.assert_graph_is_connected(g_req)
        odd_nodes = graph.get_odd_nodes(g_req)
        odd_node_pairs = list(itertools.combinations(odd_nodes, 2))
        odd_node_pairs_shortest_paths = self.get_shortest_paths_distances(g_full,
                                                                           odd_node_pairs,
                                                                           'distance')
        g_odd_complete = graph.create_complete_graph(odd_node_pairs_shortest_paths, flip_weights=True)
        odd_matching = graph.dedupe_matching(nx.algorithms.max_weight_matching(g_odd_complete, True))
        g_aug = graph.add_augmenting_path_to_graph(g_req, odd_matching)

        start_node = next(iter(required))[0]
        circuit = list(graph.create_eulerian_circuit(g_aug, g_full, start_node))

        return circuit

    def solve_fredrickson(self, required):
        """Solve using Fredrickson's heuristic"""
        g_full = self.create_graph(required)
        self.show(g_full)
        g_req = graph.create_required_graph(g_full)
        node_pairs = list(itertools.combinations(g_req, 2))
        # g_aug is the G' from Frederickson's heuristic
        # Do we use q_req or g_full here?
        g_aug = g_req.copy()
        # Add edges
        for i, pair in enumerate(node_pairs):
            try:
                d = nx.dijkstra_path_length(g_full, pair[0], pair[1], weight='distance')
                g_aug.add_edge(pair[0], pair[1], distance=d, id=-i, required=False)
            except:
                logger.exception("Dijkstra failed")

        for edge in g_aug.edges():
            # remove duplicate edges
            # actually, I think I can remove any longer edge from the parallel edges
            # (As long as they are not required).
            data = g_aug[edge[0]][edge[1]]
            if len(data) > 1:
                deletions = set()
                for pair in itertools.combinations(data.keys(), 2):
                    key1, key2 = pair
                    # FIXME: what if edge2 is required and edge1 is not???
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
                    # Remove duplicates
                    # FIXME: need to check all parallel edges
                    if g_aug[edge[0]][node][0]['distance'] - g_aug[node][edge[1]][0]['distance'] < 1e-09 \
                            and not g_aug[edge[0]][edge[1]][0]['required']:
                        #g_aug.remove_edge(edge[0], edge[1], 0)
                        deletions.add(edge)
                        break
            for edge in deletions:
                g_aug.remove_edge(edge[0], edge[1])

        T = nx.minimum_spanning_tree(g_aug, 'distance')
        if os.getenv('C42_LOGLEVEL') == 'DEBUG':
            self.show(T)
        # perhaps we need to add the required edges (again) to T, so far they were all included anyway
        # Let's test it first and then see further

        odd_nodes = graph.get_odd_nodes(T)
        odd_node_pairs = list(itertools.combinations(odd_nodes, 2))
        odd_node_pairs_shortest_paths = graph.get_shortest_paths_distances(g_full,
                                                                           odd_node_pairs,
                                                                           'distance')
        g_complete = graph.create_complete_graph(odd_node_pairs_shortest_paths, flip_weights=True)
        if os.getenv('C42_LOGLEVEL') == 'DEBUG':
            self.show(g_complete)
        M = graph.dedupe_matching(nx.algorithms.max_weight_matching(g_complete, True))
        g_aug = graph.add_augmenting_path_to_graph(T, M)

        start_node = next(iter(required))[0]
        circuit = list(graph.create_eulerian_circuit(g_aug, g_full, start_node))
        return circuit

    def mark_circuit_in_graph(self, circuit, G):
        for edge in circuit:
            from_node, to_node, _, data = edge
            try:
                if not data['required']:
                    d = G[from_node][to_node]
                    d[0]['included'] = True
            except:
                logger.warning("Unable to find edge from {} to {}. Solution will be disconnected".format(from_node, to_node))
                G.node[from_node]['color'] = 'blue'
                G.node[to_node]['color'] = 'blue'

        return G

    def show(self, G):
        plt.figure(figsize=(8, 6))
        edge_colors = ['red' if 'required' in e[2] and e[2]['required'] else 'orange' if 'included' in e[2] else 'grey' for e in G.edges(data=True)]
        node_colors = [n[1]['color'] if 'color' in n[1] else 'black' for n in G.nodes(data=True)]
        nx.draw(G, pos=self.positions, edge_color=edge_colors, node_size=3, node_color=node_colors)
        plt.show()


if __name__ == '__main__':
    import re
    pattern = re.compile(r'(\d{4}\w{2})(.*)')
    postman = Postman('map-medium.osm')
    required = set()
    addresses = []
    for arg in sys.argv[1:]:
        m = pattern.match(arg)
        if m:
            postcode, number = m.groups()
            edge = postman.find_edge_by_address(postcode, number)
            if edge:
                 required.add(tuple(sorted((edge[1], edge[2]))))
            else:
                logger.debug("arg {} not found".format(arg))
        else:
            logger.debug("invalid postcode ()".format(arg))
    G = postman.create_graph(required)
    circuit = postman.solve_fredrickson(required)
    postman.mark_circuit_in_graph(circuit, G)
    postman.show(G)

