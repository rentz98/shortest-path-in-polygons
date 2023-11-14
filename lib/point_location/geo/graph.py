class DirectedGraph:

    def __init__(self):
        self.e = {}
        self.roots = set()

    def contains(self, v):
        """Returns True if v is the list of nodes."""
        return v in self.e

    def add_node(self, v):
        """Adds a node to the graph."""
        self.e[v] = set()
        self.roots.add(v)

    def connect(self, u, v):
        """Connects the two existing nodes u -> v."""
        self.e[u].add(v)
        self.roots.discard(v)

    def is_acyclic(self):
        """Returns whether the graph has cycles."""
        # Copy data structures
        edges = {}
        for v in self.e:
            edges[v] = set([])
            for u in self.e[v]:
                edges[v].add(u)
        q = set([])
        for root in self.roots:
            q.add(root)

        while q:
            n = q.pop()
            for m in self.e[n]:
                if m not in edges[n]:
                    continue
                edges[n].remove(m)

                root = True
                for k in edges.keys():
                    if m in edges[k]:
                        root = False
                        break

                if root:
                    q.add(m)

        for k in edges.keys():
            if edges[k]:
                return False
        return True

    def neighbors(self, v):
        """Returns the neighbors of the given node."""
        return self.e[v]

    def root(self):
        """Returns one of the root nodes."""
        root = self.roots.pop()
        self.roots.add(root)
        return root


class UndirectedGraph(DirectedGraph):

    def connect(self, u, v):
        """Connects two existing nodes to one another."""
        self.e[u].add(v)
        self.e[v].add(u)

    def independent_set(self, k, avoid=None):
        """Returns independent set of nodes with degree <= k"""
        # Mark nodes w/ degree > k
        candidates = set([])
        for v in self.e:
            if len(self.e[v]) <= k:
                candidates.add(v)

        if avoid:
            candidates.difference_update(avoid)

        vertices = set([])

        while len(candidates):
            # Add new vertex to independent set
            v = candidates.pop()
            vertices.add(v)

            # Remove neighboring vertices
            candidates.difference_update(self.e[v])

        return vertices
