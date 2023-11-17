from functools import reduce
from typing import Optional

# from lib.point_location.geo import spatial
from lib.point_location.geo.spatial import convex_hull
from lib.point_location.geo.shapes import Point, Polygon, Triangle, Shape2d
from . import min_triangle
from lib.point_location.geo.graph import UndirectedGraph, DirectedGraph


class Locator(object):

    def __init__(self, regions: list[Triangle], outline=None):
        self._preprocess(regions, outline)

    def _preprocess(self, regions: list[Triangle], outline=None):
        def process_boundary(__regions: list[Triangle], __outline=None):
            """
                Adds an outer triangle and triangulates the interior region. If an outline
                for the region is not provided, uses the convex hull (thus assuming that
                the region itself is convex).

                Arguments:
                regions -- a set of non-overlapping polygons that tile some part of the plane
                outline -- the polygonal outline of regions

                Returns: a bounding triangle for regions and a triangulation for the area between
                regions and the bounding triangle.
            """
            def add_bounding_triangle(poly: Polygon):
                """
                    Calculates a bounding triangle for a polygon

                    Arguments:
                    poly -- a polygon to-be bound

                    Returns: a bounding polygon for 'poly'
                """

                bounding_tri = min_triangle.larger_bounding_triangle(poly.points)
                bounding_regions = bounding_tri.triangulate_polygon(poly.points)
                # bounding_regions = spatial.triangulate_polygon(
                #     bounding_tri, hole=poly.points)
                return bounding_tri, bounding_regions

            if not __outline:
                points = reduce(lambda ps, r: ps + r.points, __regions, [])
                __outline = convex_hull(points)
            return add_bounding_triangle(__outline)

        def triangulate_regions(__regions: list[Shape2d]):
            """
                Processes a set of regions (non-overlapping polygons tiling a portion of the plane),
                triangulating any region that is not already a triangle, and storing triangulated
                relationships in a DAG.

                Arguments:
                regions -- a set of non-overlapping polygons that tile some part of the plane

                Returns: a triangulation for each individual region in 'regions'
            """
            __frontier = []

            for region in __regions:
                self.dag.add_node(region)

                # If region is not a triangle, triangulate
                if region.n > 3 and isinstance(region, Polygon):
                    triangles = region.triangulation
                    for triangle in triangles:
                        # Connect DAG
                        self.dag.add_node(triangle)
                        self.dag.connect(triangle, region)
                        # Add to frontier
                        __frontier.append(triangle)
                elif isinstance(region, Polygon):
                    if tri := region.to_triangle():
                        __frontier.append(tri)
                    else:
                        raise ValueError(f"Region with points: {region.points} cannot be "
                                         f"converted to a triangle.")
                else:
                    __frontier.append(region)

            return __frontier

        def remove_independent_set(__regions: list[Triangle]):
            """
                Processes a set of regions, detecting and removing an independent set
                of vertices from the regions' graph representation, and re-triangulating
                the resulting holes.

                Arguments:
                regions -- a set of non-overlapping polygons that tile some part of the plane

                Returns: a new set of regions covering the same subset of the plane, with fewer vertices
            """
            # Take note of which points are in which regions
            points_to_regions = {}
            for __idx, __region in enumerate(__regions):
                for point in __region.points:
                    if point in points_to_regions:
                        points_to_regions[point].add(__idx)
                        continue

                    points_to_regions[point] = {__idx}

            # Connect graph
            g = UndirectedGraph()
            for __region in __regions:
                for __idx in range(__region.n):
                    __u = __region.points[__idx % __region.n]
                    __v = __region.points[(__idx + 1) % __region.n]
                    if not g.contains(__u):
                        g.add_node(__u)
                    if not g.contains(__v):
                        g.add_node(__v)
                    g.connect(__u, __v)

            # Avoid adding points from outer triangle
            removal = g.independent_set(8, avoid=bounding_triangle.points)

            # Track unaffected regions
            unaffected_regions = set([i for i in range(len(__regions))])
            new_regions = []
            for p in removal:
                # Take note of affected regions
                affected_regions = points_to_regions[p]
                unaffected_regions.difference_update(points_to_regions[p])

                def calculate_bounding_polygon(__p: Point, __affected_regions):
                    edges = []
                    point_locations = {}
                    for __j, __i in enumerate(__affected_regions):
                        edge = set(__regions[__i].points)
                        edge.remove(__p)
                        edges.append(edge)
                        for v in edge:
                            if v in point_locations:
                                point_locations[v].add(__j)
                            else:
                                point_locations[v] = {__j}

                    __boundary = []
                    edge = edges.pop()
                    for v in edge:
                        point_locations[v].remove(len(edges))
                        __boundary.append(v)
                    for k in range(len(__affected_regions) - 2):
                        v = __boundary[-1]
                        __i = point_locations[v].pop()
                        edge = edges[__i]
                        edge.remove(v)
                        u = edge.pop()
                        point_locations[u].remove(__i)
                        __boundary.append(u)

                    return Polygon(__boundary)

                # triangulate hole
                poly = calculate_bounding_polygon(p, affected_regions)
                triangles = poly.triangulation
                for triangle in triangles:
                    self.dag.add_node(triangle)
                    for j in affected_regions:
                        __region = __regions[j]
                        self.dag.connect(triangle, __region)
                    new_regions.append(triangle)

            for i in unaffected_regions:
                new_regions.append(__regions[i])

            return new_regions

        self.dag = DirectedGraph()

        # Store copy of regions
        self.regions = regions

        # Calculate, triangulate bounding triangle
        bounding_triangle, boundary = process_boundary(regions, outline)

        # Store copy of boundary
        self.boundary = boundary

        # Iterate until only bounding triangle remains
        frontier = triangulate_regions(regions + boundary)
        while len(frontier) > 1:
            frontier = remove_independent_set(frontier)
        return

    def locate(self, p: Point) -> Optional[Triangle]:
        """Locates the point p in one of the initial regions"""
        polygon, valid = self.annotated_locate(p)

        # Result might be valid polygon
        if not valid:
            return None

        return polygon

    def annotated_locate(self, p: Point) -> (Optional[Triangle], bool):
        """
            Locates the point p, returning the region and whether
            the region was one of the initial regions (i.e., False if the
            region was a fabricated boundary region).
        """
        curr = self.dag.root()
        if not curr.contains_point(p):
            return None, False

        children = self.dag.e[curr]
        while children:
            for region in children:
                if region.contains_point(p):
                    curr = region
                    break

            children = self.dag.e[curr]

        # Is the final region an exterior region?
        return curr, curr in self.regions
    pass
