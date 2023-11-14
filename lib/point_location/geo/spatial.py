import numpy as np
import scipy.spatial as sp

from itertools import chain
from copy import deepcopy

from . import shapes
from .shapes import Point, Polygon, Triangle
from lib.triangulation.earcut import earcut


def to_numpy(points: list[Point]):
    """Convert a list of points to a NumPy array."""
    return np.array(list(map(lambda p: p.np(), points)), np.float32)


def triangulate_polygon(poly: Polygon, hole: list[Point] = None) -> list[Triangle]:
    """Triangulates a polygon with up to one hole."""
    points_tuples = list(chain.from_iterable((p.x, p.y) for p in poly.points))
    poly_points = deepcopy(poly.points)
    hole_start_idx = None

    if hole:
        hole_start_idx = [len(points_tuples) // 2]
        poly_points += hole
        points_tuples += list(chain.from_iterable((p.x, p.y) for p in hole))

    triangles = earcut(points_tuples, hole_start_idx, 2)

    return [Triangle(poly_points[triangles[3 * i + 0]],
                     poly_points[triangles[3 * i + 1]],
                     poly_points[triangles[3 * i + 2]])
            for i in range(len(triangles) // 3)]


def triangulate_points(points: list[Point]) -> list[Triangle]:
    """Returns a triangulation of the given points (based on Delaunay algorithm)."""
    points = to_numpy(points)
    triangulation = sp.Delaunay(points)
    triangles = []
    for i in range(len(triangulation.simplices)):
        vertices = list(map(lambda p: Point(p[0], p[1]),
                            points[triangulation.simplices[i, :]]))
        triangle = Triangle(
            vertices[0], vertices[1], vertices[2])
        triangles.append(triangle)
    return triangles


def convex_hull(points: list[Point]) -> Polygon:
    """Returns the minimum-area Polygon that includes all the points given."""
    points = to_numpy(points)
    vertices = sp.ConvexHull(points).vertices
    hull = list(map(lambda idx: shapes.Point(points[idx, 0], points[idx, 1]), vertices))
    return Polygon(hull)
