import math

def percentile(data, perc: int):
    size = len(data)
    return sorted(data)[int(math.ceil((size * perc) / 100)) - 1]