from math import sqrt, ceil, floor
from typing import Optional

from .geo.shapes import Point, Line, Triangle, Polygon, ccw
from .geo.spatial import convex_hull
# from .geo.generator import random_convex_polygon
# from .geo.drawer import plot, show


def min_bounding_triangle(poly: Polygon) -> Triangle:
    """
        Returns the triangle of minimum area enclosing a convex polygon.
        Runs in Theta(n) time for convex polygons, or O(n*log(n)) for
        concave polygons as convex hull must be computed.

        Arguments:
        poly -- the polygon to be enclosed

        Returns: the triangle of minimum area enclosing polygon
    """
    if not poly.is_convex():
        poly = convex_hull(poly.points)

    n = poly.n
    points = poly.points

    # Check for degenerate cases
    if n < 3:
        raise ValueError("Polygon must have at least three vertices.")
    elif n == 3:
        return Triangle(poly.points[0], poly.points[1], poly.points[2])

    def side(idx: int) -> Line:
        """Return the side of polygon formed by vertices (idx-1) and idx."""
        return Line(points[(idx - 1) % n], points[idx % n])

    def is_valid_triangle(vertex_a: Point, vertex_b: Point, vertex_c: Point,
                          _a: int, _b: int, _c: int) -> bool:
        """Checks that a triangle composed of the given vertices is a valid local minimum."""
        if not (vertex_a and vertex_b and vertex_c):
            return False

        midpoint_a = Line(vertex_c, vertex_b).midpoint()
        midpoint_b = Line(vertex_a, vertex_c).midpoint()
        midpoint_c = Line(vertex_a, vertex_b).midpoint()

        def validate_midpoint(midpoint: Point, index: int) -> bool:
            """Checks that a midpoint touches the polygon on the appropriate side."""
            s = side(index)

            # Account for floating-point errors
            epsilon = 0.01

            if s.vertical:
                if midpoint.x != s.p1.x:
                    return False
                max_y = max(s.p1.y, s.p2.y) + epsilon
                min_y = min(s.p1.y, s.p2.y) - epsilon
                if not (max_y >= midpoint.y >= min_y):
                    return False

                return True
            else:
                max_x = max(s.p1.x, s.p2.x) + epsilon
                min_x = min(s.p1.x, s.p2.x) - epsilon
                # Must touch polygon
                if not (max_x >= midpoint.x >= min_x):
                    return False

                if not s.at_x(midpoint.x).close(midpoint):
                    return False

                return True

        return (validate_midpoint(midpoint_a, _a) and validate_midpoint(midpoint_b, _b)
                and validate_midpoint(midpoint_c, _c))

    def triangle_for_index(_c: int, _a: int, _b: int) -> tuple[Optional[Triangle], int, int]:
        """Returns the minimal triangle with edge c flush to vertex c."""
        _a = max(_a, _c + 1) % n
        _b = max(_b, _c + 2) % n
        side_c = side(_c)

        def h(point: Point | int, _side: Line) -> float:
            """Return the distance from 'point' to 'side'."""
            if isinstance(point, Point):
                return _side.distance(point)
            elif isinstance(point, int):
                return _side.distance(points[point])

        def gamma(point: Point, on: Line, base: Line) -> Point:
            """Calculate the point on 'on' that is twice as far from 'base' as 'point'."""
            intersection = on.intersection(base)
            dist = 2 * h(point, base)
            # Calculate differential change in distance
            if on.vertical:
                d_dist = h(Point(intersection.x, intersection.y + 1), base)
                guess = Point(intersection.x, intersection.y + dist / d_dist)
                if ccw(base.p1, base.p2, guess) != ccw(base.p1, base.p2, point):
                    guess = Point(intersection.x,
                                  intersection.y - dist / d_dist)
                return guess
            else:
                d_dist = h(on.at_x(intersection.x + 1), base)
                guess = on.at_x(intersection.x + dist / d_dist)
                if ccw(base.p1, base.p2, guess) != ccw(base.p1, base.p2, point):
                    guess = on.at_x(intersection.x - dist / d_dist)
                return guess

        # def critical(b, gamma_B):
        #     return ccw(gamma_B, points[b], points[(b - 1) % n]) == ccw(gamma_B, points[b], points[(b + 1) % n])

        def high(__b: int, __gamma_b: Point) -> bool:
            # Test if two adjacent vertices are on same side of line (implies
            # tangency)
            if ccw(__gamma_b, points[__b], points[(__b - 1) % n]) ==\
                    ccw(__gamma_b, points[__b], points[(__b + 1) % n]):
                return False

            # Test if Gamma and B are on same side of line from adjacent
            # vertices
            if ccw(points[(__b - 1) % n], points[(__b + 1) % n], __gamma_b) ==\
                    ccw(points[(__b - 1) % n], points[(__b + 1) % n], points[__b]):
                return h(__gamma_b, side_c) > h(__b, side_c)
            return False

        def low(__b: int, __gamma_b: Point) -> bool:
            # Test if two adjacent vertices are on same side of line (implies
            # tangency)
            if ccw(__gamma_b, points[__b], points[(__b - 1) % n]) ==\
                    ccw(__gamma_b, points[__b], points[(__b + 1) % n]):
                return False

            # Test if Gamma and B are on same side of line from adjacent
            # vertices
            if ccw(points[(__b - 1) % n], points[(__b + 1) % n], __gamma_b) ==\
                    ccw(points[(__b - 1) % n], points[(__b + 1) % n], points[__b]):
                return False
            else:
                return h(__gamma_b, side_c) > h(__b, side_c)

        def on_left_chain(__b: int) -> bool:
            return h((__b + 1) % n, side_c) >= h(__b, side_c)

        def increment_low_high(__a: int, __b: int, __c: int) -> tuple[int, int]:
            _gamma_a = gamma(points[__a], side(__a), side_c)

            if high(__b, _gamma_a):
                __b = (__b + 1) % n
            else:
                __a = (__a + 1) % n
            return __a, __b

        def tangency(__a: int, __b: int):
            _gamma_b = gamma(points[__b], side(__a), side_c)
            return h(__b, side_c) >= h((__a - 1) % n, side_c) and high(__b, _gamma_b)

        # Increment b while low
        while on_left_chain(_b):
            _b = (_b + 1) % n

        # Increment _a if low, _b if high
        while h(_b, side_c) > h(_a, side_c):
            _a, _b = increment_low_high(_a, _b, _c)

        # Search for b tangency
        while tangency(_a, _b):
            _b = (_b + 1) % n

        gamma_b = gamma(points[_b], side(_a), side_c)
        # Adjust if necessary
        if low(_b, gamma_b) or h(_b, side_c) < h((_a - 1) % n, side_c):
            side_b = side(_b)
            side_a = side(_a)
            side_b = Line(side_c.intersection(side_b),
                          side_a.intersection(side_b))

            if h(side_b.midpoint(), side_c) < h((_a - 1) % n, side_c):
                gamma_a = gamma(points[(_a - 1) % n], side_b, side_c)
                side_a = Line(gamma_a, points[(_a - 1) % n])
        else:
            gamma_b = gamma(points[_b], side(_a), side_c)
            side_b = Line(gamma_b, points[_b])
            side_a = Line(gamma_b, points[(_a - 1) % n])

        # Calculate final intersections
        vertex_a = side_c.intersection(side_b)
        vertex_b = side_c.intersection(side_a)
        vertex_c = side_a.intersection(side_b)

        # Check if triangle is valid local minimum
        if not is_valid_triangle(vertex_a, vertex_b, vertex_c, _a, _b, _c):
            _triangle = None
        else:
            _triangle = Triangle(vertex_a, vertex_b, vertex_c)

        return _triangle, _a, _b

    triangles = []
    a = 1
    b = 2
    for i in range(n):
        triangle, a, b = triangle_for_index(i, a, b)
        if triangle:
            triangles.append(triangle)

    areas = [triangle.area() for triangle in triangles]
    return triangles[areas.index(min(areas))]


def larger_bounding_triangle(points: list[Point], factor: int = 10) -> Polygon:
    def expand(poly: Polygon, _factor: int) -> Polygon:
        """Expands a polygon, moving the vertices outward ~'factor'."""
        def bisect(__a: Point, __b: Point, __c: Point) -> Point:
            # Define vector operations
            def magnitude(__v: list[float]) -> float:
                return sqrt(sum([__x * __x for __x in __v]))

            def normalize(__v: list[float]) -> list[float]:
                mag = magnitude(__v)
                return [__x / mag for __x in __v]

            def median(__u: list[float], __v: list[float]):
                return [(__x[0] + __x[1]) / 2 for __x in zip(__u, __v)]

            def reverse(__v: list[float]):
                return [-__x for __x in __v]

            # Form vectors
            v_b = [__b.x - __a.x, __b.y - __a.y]
            v_c = [__c.x - __a.x, __c.y - __a.y]
            v_b = normalize(v_b)
            v_c = normalize(v_c)
            bisector = reverse(median(v_b, v_c))

            x = __a.x + _factor * bisector[0]
            y = __a.y + _factor * bisector[1]

            def abs_round(n: float) -> int:
                if n < 0:
                    return floor(n)
                return ceil(n)

            x = abs_round(x)
            y = abs_round(y)

            return Point(x, y)

        def adjust(i: int) -> Point:
            __a = poly.points[i % poly.n]
            __b = poly.points[(i - 1) % poly.n]
            __c = poly.points[(i + 1) % poly.n]
            return bisect(__a, __b, __c)

        expanded_points = [adjust(i) for i in range(poly.n)]
        return Polygon(expanded_points)

    return expand(min_bounding_triangle(Polygon(points)), factor)


# if __name__ == "__main__":
#     _poly = random_convex_polygon(10)
#     tri = min_triangle(_poly)
#     plot(_poly)
#     show(tri, style='r--')
