from random import random
from queue import PriorityQueue

from lib.point_location.geo.shapes import Point, Polygon
from lib.point_location.geo.spatial import convex_hull


def random_point(k=None) -> Point:
    """Create a random point scaled with k"""
    if k:
        return Point(int(k * random()), int(k * random()))
    return Point(random(), random())


def random_convex_polygon(sample, k=None, n=3):
    """Creates a random convex polygon with n angles scaled with k"""
    hull = convex_hull([random_point(k=k) for _ in range(sample)])
    while hull.n < n:
        hull = convex_hull([random_point(k=k) for _ in range(sample)])
    return hull


def random_tiling(polygon: Polygon, n: int, is_concave=False) -> list[Polygon]:
    """Generates a random concave tiling of a convex region."""
    class PolygonWithArea(object):

        def __init__(self, _polygon: Polygon):
            self.polygon = _polygon
            self.area = _polygon.area()

        def __cmp__(self, that):
            return super().__cmp__(self.area, that.area)

    # Start with initial convex region
    initial = PolygonWithArea(polygon)

    # Place in PQ to pop by area
    pq = PriorityQueue(maxsize=n + 1)
    pq.put(initial)

    # Create some concave regions
    triangles = []
    for i in range(n):
        # Split up largest polygon
        polygon = pq.get().polygon

        for polygon in polygon.split(interior=is_concave):
            if polygon.n == 3:
                triangles.append(polygon)
            else:
                pq.put(PolygonWithArea(polygon))

    polygons = triangles
    while pq.qsize():
        polygons.append(pq.get().polygon)

    return polygons


def random_concave_tiling(polygon, n=10):
    return random_tiling(polygon, n=n, is_concave=True)


def random_convex_tiling(polygon, n=10):
    return random_tiling(polygon, n)
