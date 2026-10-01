THIRD_EDGES = [(-52.5, -17.5, "defensive"), (-17.5, 17.5, "middle"), (17.5, 52.5, "attacking")]

def third_of(x: float) -> str | None:
    for lo, hi, name in THIRD_EDGES:
        if lo <= x < hi:
            return name
    # The attacking third is closed at +52.5 by the brief.
    if x == 52.5:
        return "attacking"
    return None
