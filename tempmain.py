import shapefile

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from lib.triangulation.earcut import flatten, earcut, deviation
from lib.point_location.geo.shapes import Point, Polygon, Triangle
from lib.point_location.kirkpatrick import SinglePolygonLocator
from lib.path_finding.path_tools import DCEL

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
locator = SinglePolygonLocator(regions=triangles_polygon, outline=outline_polygon)

dcel = DCEL(triangles_polygon)


def calc_path(p1: Point, p2: Point, region1: Triangle = None, region2: Triangle = None):

    if not region1:
        region1 = locator.locate(p1)
    if not region2:
        region2 = locator.locate(p2)

    if not region1 or not region2:
        return

    res = dcel.bfs(region1, region2)
    tmp, tmp2 = dcel.funnel(res, p1, p2)
    pres = dcel.presentable_form(res)
    # for i in pres:
    #     plt.plot(i['x'], i['y'], 'r-')
    # for i in tmp:
    #     plt.plot(i['x'], i['y'], 'k-')
    plt.plot(tmp2['x'], tmp2['y'], 'g-')
    return


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
        return

    one_point = not one_point

    if one_point:
        old_point = point
        old_triangle_region = triangle_region
    else:
        calc_path(old_point, point, old_triangle_region, triangle_region)

    # target_region = locator.locate(point)
    plt_x = [p.x for p in triangle_region.points]
    plt_y = [p.y for p in triangle_region.points]
    plt_x.append(plt_x[0])
    plt_y.append(plt_y[0])
    # plt.plot(plt_x, plt_y, 'r-')
    plt.plot(ex, ey, 'k.')
    plt.show()
    pass



# p1 = Point(33.277286178158604, 30.731894537297677)
# p2 = Point(22.07027392547043, 37.51042409394792)
# p1 = Point(127.55627675389786, 36.1116798997185)
# p2 = Point(49.527453944556456, 19.541940983462347)
# p2 = Point(127.55627675389786, 36.1116798997185)
# p1 = Point(49.527453944556456, 19.541940983462347)

# p2 = Point(28.934568930241937, 63.65618095531315)
# p1 = Point(-0.904101192540324, 38.80157258092892)

# p1 = Point(6.2403691185483865, 60.858692566854316)
# p2 = Point(-0.904101192540324, 38.80157258092892)
# p2 = Point(6.2403691185483865, 60.858692566854316)
# p1 = Point(-0.904101192540324, 38.80157258092892)
#
# p1 = Point(55.971485989852155, 25.029322053131594)
# p2 = Point(82.44805243682796, 73.33979460767064)
# p2 = Point(55.971485989852155, 25.029322053131594)
# p1 = Point(82.44805243682796, 73.33979460767064)
# calc_path(p1, p2)

fig.canvas.mpl_connect('button_press_event', onclick)
# fig.show()
plt.show()
