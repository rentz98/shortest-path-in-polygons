from random import random
from math import sqrt
from typing import Optional
from abc import ABC, abstractmethod

from itertools import chain
from copy import deepcopy
# from .spatial import triangulate_polygon

from lib.triangulation.earcut import earcut


class Point(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __add__(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def __rmul__(self, c):
        return Point(c * self.x, c * self.y)

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def close_to(self, other, epsilon=0.01):
        return self.dist(other) < epsilon

    def dist(self, other):
        return sqrt(self.sqr_dist(other))

    def sqr_dist(self, other):
        dx = self.x - other.x
        dy = self.y - other.y
        return dx * dx + dy * dy

    def np(self):
        """Returns the point's Numpy point representation"""
        return [self.x, self.y]


def ccw(a: Point, b: Point, c: Point):
    """Tests whether the line formed by A, B, and C is ccw"""
    return (b.x - a.x) * (c.y - a.y) > (b.y - a.y) * (c.x - a.x)


def intersect(a1, b1, a2, b2):
    """Returns True if the line segments a1b1 and a2b2 intersect."""
    return (ccw(a1, b1, a2) != ccw(a1, b1, b2)
            and ccw(a2, b2, a1) != ccw(a2, b2, b1))


class Line:

    def __init__(self, p1: Point, p2: Point):
        self.p1 = p1
        self.p2 = p2

        if p1.x == p2.x:
            self.slope = None
            self.intercept = None
            self.vertical = True
        else:
            self.slope = float(p2.y - p1.y) / (p2.x - p1.x)
            self.intercept = p1.y - self.slope * p1.x
            self.vertical = False

    def __str__(self) -> str:
        if self.vertical:
            return "x = " + str(self.p1.x)
        return "y = " + str(self.slope) + "x + " + str(self.intercept)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Line):
            return False

        if self.vertical != other.vertical:
            return False

        if self.vertical:
            return self.p1.x == other.p1.x

        return self.slope == other.slope and self.intercept == other.intercept

    def at_x(self, x: float) -> Optional[Point]:
        """Returns the point in the line at with the given value as the x part."""
        if self.vertical:
            return None

        return Point(x, self.slope * x + self.intercept)

    def _sqr_distance(self, p: Point) -> float:
        """Distance of given point from the line squared."""
        numerator = float(self.p2.x - self.p1.x) * (self.p1.y - p.y) - \
            (self.p1.x - p.x) * (self.p2.y - self.p1.y)
        numerator *= numerator
        denominator = float(self.p2.x - self.p1.x) * (self.p2.x - self.p1.x) + \
            (self.p2.y - self.p1.y) * (self.p2.y - self.p1.y)
        return numerator / denominator

    def distance(self, p: Point) -> float:
        """Returns the distance of p from the line"""
        return sqrt(self._sqr_distance(p))

    def intersection(self, other) -> Optional[Point]:
        """Returns the point of the intersection of this and the given lines."""
        if not isinstance(other, Line):
            return None

        if other.slope == self.slope:
            return None

        if self.vertical:
            return other.at_x(self.p1.x)
        elif other.vertical:
            return self.at_x(other.p1.x)

        x = float(self.intercept - other.intercept) / (other.slope - self.slope)
        return self.at_x(x)

    def midpoint(self) -> Point:
        """Returns the midpoint of the line segment."""
        x = float(self.p1.x + self.p2.x) / 2
        y = float(self.p1.y + self.p2.y) / 2
        return Point(x, y)


class Shape2d(ABC):

    def __init__(self, points: list[Point]):
        if len(points) < 3:
            raise ValueError("Polygon must have at least three vertices.")

        self.points = points
        self.n = len(points)
        self.__hash = None
        pass

    def __str__(self) -> str:
        s = ""
        for point in self.points:
            if s:
                s += " -> "
            s += str(point)
        return s

    def __hash__(self):
        return self.hash

    @property
    def hash(self):
        if self.__hash:
            return self.__hash
        return hash(tuple(sorted(self.points, key=lambda p: p.x)))

    def reset_hash(self):
        self.__hash = None

    @property
    def x(self) -> list[float]:
        return [p.x for p in self.points] + [self.points[0].x]

    @property
    def y(self) -> list[float]:
        return [p.y for p in self.points] + [self.points[0].y]

    @abstractmethod
    def contains_point(self, point: Point) -> bool:
        pass

    def _convex_contains_point(self, p: Point) -> bool:
        # If convex, use CCW-esque algorithm
        is_inside = False

        p1 = self.points[0]
        for i in range(self.n + 1):
            p2 = self.points[i % self.n]
            if p.y > min(p1.y, p2.y):
                if p.y <= max(p1.y, p2.y):
                    if p.x <= max(p1.x, p2.x):
                        x_ints = float('-inf')
                        if p1.y != p2.y:
                            x_ints = (p.y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y) + p1.x
                        if p1.x == p2.x or p.x <= x_ints:
                            is_inside = not is_inside
            p1 = p2
        return is_inside
    pass


class Triangle(Shape2d):

    def __init__(self, a: Point, b: Point, c: Point):
        self.a = a
        self.b = b
        self.c = c
        super(Triangle, self).__init__([a, b, c])

    def area(self) -> float:
        a = self.a
        b = self.b
        c = self.c
        return (abs((b.x * a.y - a.x * b.y)
                    + (c.x * b.y - b.x * c.y)
                    + (a.x * c.y - c.x * a.y)) / 2.0)

    def interior_point(self):
        # Different and faster way to compute a random interior point.
        a = self.a
        b = self.b
        c = self.c
        r1 = random()
        r2 = random()
        return (1 - sqrt(r1)) * a + sqrt(r1) * (1 - r2) * b + r2 * sqrt(r1) * c

    def contains_point(self, point: Point) -> bool:
        return self._convex_contains_point(point)
    pass


class Polygon(Shape2d):

    def __init__(self, points: list[Point]):
        if len(points) < 3:
            raise ValueError("Polygon must have at least three vertices.")

        self._triangulation: Optional[list[Triangle]] = None
        self.hole: Optional[list[Point]] = None
        super(Polygon, self).__init__(points)

    @property
    def triangulation(self) -> list[Triangle]:
        if self._triangulation:
            return self._triangulation
        return self.triangulate_polygon(self.hole)

    def triangulate_polygon(self, hole: list[Point] = None) -> list[Triangle]:
        """Triangulates a polygon with up to one hole."""
        points_tuples = list(chain.from_iterable((p.x, p.y) for p in self.points))
        poly_points = deepcopy(self.points)
        hole_start_idx = None

        if hole:
            hole_start_idx = [len(points_tuples) // 2]
            poly_points += hole
            points_tuples += list(chain.from_iterable((p.x, p.y) for p in hole))

        triangles = earcut(points_tuples, hole_start_idx, 2)

        self._triangulation = [Triangle(poly_points[triangles[3 * i + 0]],
                               poly_points[triangles[3 * i + 1]],
                               poly_points[triangles[3 * i + 2]])
                               for i in range(len(triangles) // 3)]
        return self._triangulation

    def contains_point(self, p: Point) -> bool:
        """Returns True if p is inside the Polygon."""
        if self.is_convex():
            return self._convex_contains_point(p)
        else:
            # If concave, must triangulate and check individual triangles
            triangles = self.triangulation
            for triangle in triangles:
                if triangle.contains_point(p):
                    return True
            return False

    def is_convex(self) -> bool:
        target = None
        for i in range(self.n):
            # Check every triplet of points
            a = self.points[i % self.n]
            b = self.points[(i + 1) % self.n]
            c = self.points[(i + 2) % self.n]

            if not target:
                target = ccw(a, b, c)
            else:
                if ccw(a, b, c) != target:
                    return False

        return True

    def ccw(self) -> bool:
        """Returns True if the points are provided in CCW order."""
        return ccw(self.points[0], self.points[1], self.points[2])

    def split(self, interior=False):
        """
            Randomly splits the polygon in two. If INTERIOR, then the split is created
            by introducing a random interior point and connecting two random vertices
            to the interior point. Else, two random vertices are themselves connected.
        """
        def random_split():
            def draw():
                # Randomly choose two vertices to connect
                _u = int(random() * self.n)
                _v = int(random() * self.n)
                if interior:
                    while _u == _v:
                        _v = int(random() * self.n)
                else:
                    while abs(_v - _u) < 2 or abs(_u - _v) > self.n - 2:
                        _v = int(random() * self.n)

                # W.L.O.G., set u to be min
                return min(_u, _v), max(_u, _v)

            u, v = draw()

            # Split points based on vertices
            p1 = self.points[u:v + 1]
            p2 = self.points[v:] + self.points[:u + 1]

            if interior:
                # Pick a random interior point
                p = self.smart_interior_point()
            else:
                p = None

            while not valid_choice(u, v, p):
                u, v = draw()
                # Split points based on vertices
                p1 = self.points[u:v + 1]
                p2 = self.points[v:] + self.points[:u + 1]
                if interior:
                    p = self.smart_interior_point()

            if interior:
                return Polygon(p1 + [p]), Polygon(p2 + [p])
            else:
                return Polygon(p1), Polygon(p2)

        def valid_choice(u, v, p):
            """Returns True if choice u, v, p keeps polygons simple, non-intersecting."""
            p_u = self.points[u]
            p_v = self.points[v]
            for i in range(self.n):
                p1 = self.points[i]
                p2 = self.points[(i + 1) % self.n]

                if p:
                    if p1 != p_u and p2 != p_u:
                        if intersect(p_u, p, p1, p2):
                            return False
                    if p1 != p_v and p2 != p_v:
                        if intersect(p_v, p, p1, p2):
                            return False
                else:
                    if p1 == p_u or p2 == p_u or p1 == p_v or p2 == p_v:
                        continue
                    if intersect(p_v, p_u, p1, p2):
                        return False
            return True

        # No need to check for overflow with a convex split
        if self.is_convex():
            return random_split()

        poly1, poly2 = random_split()
        # If area has increased, invalid selection
        while poly1.area() + poly2.area() > self.area():
            poly1, poly2 = random_split()
        return poly1, poly2

    def area(self) -> float:
        """Returns the area of the polygon."""
        triangles = self.triangulation
        areas = [t.area() for t in triangles]
        return sum(areas)

    def interior_point(self) -> Point:
        """Returns a random point interior point via rejection sampling."""
        min_x = min([p.x for p in self.points])
        max_x = max([p.x for p in self.points])
        min_y = min([p.y for p in self.points])
        max_y = max([p.y for p in self.points])

        def x():
            return min_x + random() * (max_x - min_x)

        def y():
            return min_y + random() * (max_y - min_y)

        p = Point(x(), y())
        while not self.contains_point(p):
            p = Point(x(), y())

        return p

    def exterior_point(self) -> Point:
        """Returns a random exterior point near the polygon."""
        min_x = min([p.x for p in self.points])
        max_x = max([p.x for p in self.points])
        min_y = min([p.y for p in self.points])
        max_y = max([p.y for p in self.points])

        def off():
            return 1 - 2 * random()

        def x():
            return min_x + random() * (max_x - min_x) + off()

        def y():
            return min_y + random() * (max_y - min_y) + off()

        p = Point(x(), y())
        while self.contains_point(p):
            p = Point(x(), y())

        return p

    def smart_interior_point(self):
        """Returns a random interior point via triangulation."""
        triangles = self.triangulation
        areas = [t.area() for t in triangles]
        total = sum(areas)
        probabilities = [area / total for area in areas]

        # Sample triangle according to area
        r = random()
        count = 0
        for (triangle, prob) in zip(triangles, probabilities):
            count += prob
            if count >= r:
                return triangle.interior_point()

    def to_triangle(self) -> Optional[Triangle]:
        if self.n == 3:
            return Triangle(*self.points)
    pass
