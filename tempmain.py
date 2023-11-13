import shapefile

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from lib.triangulation.earcut import flatten, earcut, deviation
from lib.point_location.geo.shapes import Point, Polygon, Triangle
from lib.point_location.kirkpatrick import Locator
from lib.path_finding.path_tools import DCEL_esque

fig = plt.figure()

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
d = deviation(flatten_dict['vertices'], [], 2, tri)
points = flatten_dict["vertices"]


plt.plot(poly_coords_x, poly_coords_y, 'b-')
triangles_points = [[poly_points[tri[3*i + 0]], poly_points[tri[3*i + 1]], poly_points[tri[3*i + 2]]]
                    for i in range(len(tri) // 3)]
# for t in triangles_points:
#     plt.plot([t[0].x, t[2].x], [t[0].y, t[2].y], 'k-')
#     plt.plot([t[1].x, t[0].x], [t[1].y, t[0].y], 'k-')
#     plt.plot([t[2].x, t[1].x], [t[2].y, t[1].y], 'k-')
outline_points = poly_points + [poly_points[0]]
outline_polygon = Polygon(poly_points)
triangles_polygon = [Triangle(*p) for p in triangles_points]
locator = Locator(regions=triangles_polygon, outline=outline_polygon)

dcel = DCEL_esque(triangles_polygon, locator)

one_point = False
old_point = None

old_triangle_region = None
def onclick(event):
    global ex, ey, one_point, old_point, old_triangle_region

    ex, ey = event.xdata, event.ydata

    print(f'received user coordinates: {ex}, {ey}')
    point = Point(ex, ey)
    triangle_region = locator.locate(point)


    if not triangle_region:
        print("Invalid point")

    one_point = not one_point

    if one_point:
        old_point = point
        old_triangle_region = triangle_region
    else:
        res = dcel.bfs(old_triangle_region, triangle_region)
        tmp, tmp2 = dcel.funnel(old_triangle_region, res, old_point, point)
        pres = dcel.presentable_form(res)
        for i in pres:
            plt.plot(i['x'], i['y'], 'r-')
        plt.plot(tmp2['x'], tmp2['y'], 'g-')

    # target_region = locator.locate(point)
    plt_x = [p.x for p in triangle_region.points]
    plt_y = [p.y for p in triangle_region.points]
    plt_x.append(plt_x[0])
    plt_y.append(plt_y[0])
    plt.plot(plt_x, plt_y, 'r-')
    plt.plot(ex, ey, 'k.')
    plt.show()
    pass


fig.canvas.mpl_connect('button_press_event', onclick)

# fig.show()
plt.show()
