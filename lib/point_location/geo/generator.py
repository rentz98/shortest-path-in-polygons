from random import random
from queue import Queue

from lib.point_location.geo.shapes import Point, Polygon
from lib.point_location.geo.spatial import convex_hull


def random_point(k=None):
    if k:
        return Point(int(k * random()), int(k * random()))
    return Point(random(), random())


def random_convex_polygon(sample, k=None, n=3):
    hull = convex_hull([random_point(k=k) for i in range(sample)])
    while hull.n < n:
        hull = convex_hull([random_point(k=k) for i in range(sample)])
    return hull


def random_tiling(polygon: Polygon, n: int, CONCAVE=False):
    """Generates a random concave tiling of a convex region."""
    class PolygonWithArea(object):

        def __init__(self, polygon: Polygon):
            self.polygon = polygon
            self.area = polygon.area()

        def __cmp__(self, that):
            return -cmp(self.area, that.area)

    # Start with initial convex region
    initial = PolygonWithArea(polygon)

    # Place in PQ to pop by area
    pq = Queue.PriorityQueue(maxsize=n + 1)
    pq.put(initial)

    # Create some concave regions
    triangles = []
    for i in range(n):
        # Split up largest polygon
        polygon = pq.get().polygon

        for polygon in polygon.split(interior=CONCAVE):
            if polygon.n == 3:
                triangles.append(polygon)
            else:
                pq.put(PolygonWithArea(polygon))

    polygons = triangles
    while pq.qsize():
        polygons.append(pq.get().polygon)

    return polygons


def randomConcaveTiling(polygon, n=10):
    return random_tiling(polygon, n=n, CONCAVE=True)


def randomConvexTiling(polygon, n=10):
    return random_tiling(polygon, n)
