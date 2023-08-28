import numpy as np
import scipy.spatial as sp

from itertools import chain
from copy import deepcopy

# from p2t import CDT

from . import shapes
from lib.triangulation.earcut import earcut


def toNumpy(points):
    return np.array(list(map(lambda p: p.np(), points)), np.float32)


def triangulatePolygon(poly, hole=None):
    points_tuples = list(chain.from_iterable((p.x, p.y) for p in poly.points))
    poly_points = deepcopy(poly.points)
    hole_start_idx = None

    if hole:
        hole_start_idx = [len(points_tuples) // 2]
        poly_points += hole
        points_tuples += list(chain.from_iterable((p.x, p.y) for p in hole))

    triangles = earcut(points_tuples, hole_start_idx, 2)

    return [shapes.Triangle(poly_points[triangles[3 * i + 0]],
                            poly_points[triangles[3 * i + 1]],
                            poly_points[triangles[3 * i + 2]])
            for i in range(len(triangles) // 3)]


def triangulatePoints(points):
    points = toNumpy(points)
    triangulation = sp.Delaunay(points)
    triangles = []
    for i in range(len(triangulation.simplices)):
        verts = list(map(lambda p: shapes.Point(p[0], p[1]),
                         points[triangulation.simplices[i, :]]))
        triangle = shapes.Triangle(
            verts[0], verts[1], verts[2])
        triangles.append(triangle)
    return triangles


def convexHull(points):
    points = toNumpy(points)
    verts = sp.ConvexHull(points).vertices
    hull = list(map(lambda idx: shapes.Point(points[idx, 0], points[idx, 1]), verts))
    return shapes.Polygon(hull)
