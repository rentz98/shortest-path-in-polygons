from . import spatial
import matplotlib.pyplot as plt


def plot_points(points, style='bo'):
    if not type(points) == list:
        points = [points]

    points = spatial.to_numpy(points)
    plt.plot(points[:, 0], points[:, 1], style)


def show_points(points, style='bo'):
    plot_points(points, style=style)
    plt.show()


def plot(polygons, style='g-'):
    if not type(polygons) == list:
        polygons = [polygons]
    for polygon in polygons:
        points = polygon.points + [polygon.points[0]]
        plot_points(points, style=style)


def show(polygons, style='g-'):
    plot(polygons, style=style)
    plt.show()
