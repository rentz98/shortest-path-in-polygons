from lib.point_location.geo.shapes import Point
from lib.point_location.kirkpatrick import Locator
from lib.point_location.geo.shapes import ccw


def point_hash(p1: Point, p2: Point):
    return hash(hash(p1) + hash(p2))


class DCEL_esque:
    def __init__(self, triangles, locator: Locator):
        self.locator = locator
        self.triangles = dict()
        self.edges = dict()
        self.create_graph(triangles)
        return

    def create_graph(self, triangles):
        for t in triangles:
            edges = []
            neighbors = []
            this_triangle_hash = hash(t)
            for i in range(3):
                hash_e = point_hash(t.points[i], t.points[(i + 1) % 3])
                if hash_e not in self.edges.keys():
                    self.edges[hash_e] = Edge(t.points[i], t.points[(i + 1) % 3], this_triangle_hash)
                else:
                    other_triangle_hash = self.edges[hash_e].add_triangle(t)
                    neighbors.append(other_triangle_hash)
                    self.triangles[other_triangle_hash]['neighbours'].append(this_triangle_hash)
                edges.append(hash_e)
            self.triangles[this_triangle_hash] = {'triangle': t, 'edges': edges, 'neighbours': neighbors}
        return

    def bfs(self, p1_triangle:Point, p2_triangle:Point):
        p1_hash = hash(p1_triangle)
        p2_hash = hash(p2_triangle)

        graph = self.triangles
        visited = [p1_hash]
        queue = [p1_hash]

        traversal = {p1_hash: None}

        while queue:
            s = queue.pop(0)
            print('current triangle hash:', s)

            if s == p2_hash:
                return self.retrive_path(traversal, s)

            for neighbour in graph[s]['neighbours']:
                if neighbour not in visited:
                    traversal[neighbour] = s
                    visited.append(neighbour)
                    queue.append(neighbour)

    def retrive_path(self, graph, s):
        node = s
        path = []
        while True:
            if node not in graph:
                return []

            path.append(node)
            if graph[node] is None:
                return list(reversed(path))

            node = graph[node]

    def presentable_form(self, triangle_hashes):
        triangles = []
        for h in triangle_hashes:
            t = self.triangles[h]['triangle']
            triangles.append({'x': [p.x for p in t.points], 'y': [p.y for p in t.points]})
        return triangles

    def retrieve_triangles(self, triangle_hashes):
        return [self.triangles[h]['triangle'] for h in triangle_hashes]

    def funnel(self, triangle_path, triangle_hashes, start: Point, end: Point):
        tail = []
        right = []
        left = []

        edges = []
        for i in range(len(triangle_hashes) - 1):
            edge_hash = self.compare_lists(self.triangles[triangle_hashes[i]]['edges'],
                                           self.triangles[triangle_hashes[i + 1]]['edges'])
            edges.append(self.edges[edge_hash])

        tmp = []
        for e in edges:
            tmp.append({'x': [e.p1.x, e.p2.x, e.p1.x], 'y': [e.p1.y, e.p2.y, e.p1.y]})

        tail.append(start)

        for edge in edges:
            pl, pr = edge.p1, edge.p2
            if not ccw(pl, tail[-1], pr):
                pl, pr = pr, pl
            if pl != left[-1]:
                left.append(pl)
            if pr != right[-1]:
                left.append(pr)

        return tmp

    def compare_lists(self, l1, l2):
        for i in l1:
            for j in l2:
                if i == j:
                    return i
        return None


class Edge:
    def __init__(self, p1: Point, p2: Point, triangle):
        self.p1 = p1
        self.p2 = p2
        if triangle is None:
            raise ValueError("Received None")
        self.triangles = [triangle]
        return

    def __hash__(self):
        return point_hash(self.p1, self.p2)

    def add_triangle(self, triangle):
        if len(self.triangles) > 1:
            raise IndexError("Attempted to assign a third triangle to an edge")
        self.triangles.append(triangle)
        return self.triangles[0]
