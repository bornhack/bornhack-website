# TODO: docstrings because what the hell is going on here
from __future__ import annotations


def adjust_color(color, factor=0.4):
    if len(color) == 3:
        color = (*color, 1)
    r, g, b, a = color
    if factor > 0:
        new_r = int(min(255, r + (255 - r) * factor))
        new_g = int(min(255, g + (255 - g) * factor))
        new_b = int(min(255, b + (255 - b) * factor))
    else:
        factor = factor * -1
        new_r = int(max(0, r - r * factor))
        new_g = int(max(0, g - g * factor))
        new_b = int(max(0, b - b * factor))

    return (new_r, new_g, new_b, a)


def is_dark(color):
    return 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2] < 150


def is_light(color):
    return 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2] > 150
