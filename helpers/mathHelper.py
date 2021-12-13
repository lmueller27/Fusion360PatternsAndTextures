import math, random

def percentile(data, perc: int):
    size = len(data)
    return sorted(data)[int(math.ceil((size * perc) / 100)) - 1]

def lerp(lo, hi, t):
    return lo * (1 - t) + hi * t

def smoothstep(t):
    return t * t * (3 - 2 * t)
