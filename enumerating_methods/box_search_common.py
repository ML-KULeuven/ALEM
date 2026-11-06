"""Solver-independent data structures for objective-space box search."""

from dataclasses import dataclass
from typing import Iterable


Point = tuple[int, ...]


def update_upper_bounds(bounds: Iterable[Point], point: Point) -> list[Point]:
    candidates: set[Point] = set()
    for upper in bounds:
        if all(point[i] < upper[i] for i in range(len(point))):
            for i in range(len(point)):
                child = list(upper)
                child[i] = point[i]
                candidates.add(tuple(child))
        else:
            candidates.add(upper)
    return sorted(
        upper for upper in candidates
        if not any(
            upper != other and all(upper[i] <= other[i] for i in range(len(upper)))
            for other in candidates
        )
    )


@dataclass
class SearchResult:
    points: list[Point]
    upper_bounds: list[Point]
    ideal: Point
    complete: bool
    stop_reason: str
    elapsed_seconds: float
    solves: int
