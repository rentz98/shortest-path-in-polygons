import shapefile
import matplotlib.pyplot as plt

from lib.triangulation.earcut import flatten, earcut
from lib.point_location.geo.shapes import Point, Polygon, Triangle
from lib.point_location.kirkpatrick import Locator
from lib.path_finding.path_tools import DCEL_esque

# fig = plt.figure()

# for i, filename in enumerate(["GSHHS_c_L1", "GSHHS_h_L1", "GSHHS_i_L1", "GSHHS_l_L1", ]):
with shapefile.Reader(f"data/GSHHS_c_L1.shp") as reader:
    shapes = reader.shapes()
    pass
    
# for island in shapes:
island = shapes[0]
tmp_x = []
tmp_y = []

poly_points = [Point(p[0], p[1]) for p in island.points]
poly_coords_x = [p[0] for p in island.points]
poly_coords_y = [p[1] for p in island.points]

flatten_dict = flatten([island.points])
tri = earcut(flatten_dict['vertices'], flatten_dict['holes'], flatten_dict['dimensions'])
points = flatten_dict["vertices"]


plt.plot(poly_coords_x, poly_coords_y, 'b-')
triangles_points = [[poly_points[tri[3*i + 0]], poly_points[tri[3*i + 1]], poly_points[tri[3*i + 2]]]
                    for i in range(len(tri) // 3)]
for t in triangles_points:
    plt.plot(t[0].x, t[0].y, 'k')
    plt.plot(t[1].x, t[1].y, 'k')
    plt.plot(t[2].x, t[2].y, 'k')

# fig.show()
plt.show()
