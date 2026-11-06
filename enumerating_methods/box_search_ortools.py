"""OR-Tools CP-SAT backend for integer objective-space box search."""

from __future__ import annotations

from math import gcd, log
from time import perf_counter
from typing import Callable, Sequence

from cpmpy import Model, SolverLookup, intvar
from cpmpy.solvers.solver_interface import ExitStatus

from enumerating_methods.box_search_common import Point, SearchResult, update_upper_bounds


def _lcm(a: int, b: int) -> int:
    return abs(a * b) // gcd(a, b)


class IntegerBoxSearchORTools:
    """Exact bounded box search using fresh CP-SAT submodels.

    CP-SAT only accepts integer linear constraints. The normalized augmented
    Chebyshev scalarization is therefore multiplied by the exact LCM of all
    objective spans; no floating-point approximation is introduced.
    """

    def __init__(self, base_model: Model, objectives: Sequence,
                 objective_lower: Sequence[int], objective_upper: Sequence[int]):
        self.base_model = base_model
        self.objectives = tuple(objectives)
        self.lower = tuple(map(int, objective_lower))
        self.initial_upper = tuple(int(x) + 1 for x in objective_upper)

    @staticmethod
    def _priority(upper: Point, ideal: Point) -> float:
        return sum(log(max(1, upper[i] - ideal[i])) for i in range(len(upper)))

    def _solve(self, constraints, objective, deadline: float, threads: int):
        remaining = deadline - perf_counter()
        if remaining <= 0:
            raise TimeoutError
        model = Model(list(self.base_model.constraints) + list(constraints), minimize=objective)
        solver = SolverLookup.get("ortools", model)
        solved = solver.solve(time_limit=remaining, num_workers=threads,
                              log_search_progress=False)
        status = solver.status().exitstatus
        if status == ExitStatus.OPTIMAL:
            return tuple(int(round(obj.value())) for obj in self.objectives)
        if status == ExitStatus.UNSATISFIABLE:
            return None
        raise TimeoutError(f"CP-SAT subproblem not proven optimal: {status.name}")

    def compute_ideal(self, deadline: float, threads: int):
        ideal = []
        for objective in self.objectives:
            point = self._solve([], objective, deadline, threads)
            if point is None:
                raise RuntimeError("base land model is infeasible")
            ideal.append(point[len(ideal)])
        return tuple(ideal), len(self.objectives)

    def _solve_box(self, upper: Point, ideal: Point, deadline: float, threads: int):
        bounds = [obj <= upper[i] - 1 for i, obj in enumerate(self.objectives)]
        spans = [max(1, upper[i] - ideal[i]) for i in range(len(upper))]
        scale = 1
        for span in spans:
            scale = _lcm(scale, span)
            if scale > 10**12:
                raise OverflowError("objective-span LCM is too large for safe CP-SAT scaling")
        coefficients = [scale // span for span in spans]
        normalized = [
            coefficients[i] * (obj - ideal[i])
            for i, obj in enumerate(self.objectives)
        ]
        lambda_scaled = intvar(0, scale, name="box_lambda_scaled")
        scalar_constraints = [lambda_scaled >= term for term in normalized]
        augmentation_bound = 1 + sum(
            coefficients[i] * (upper[i] - ideal[i]) for i in range(len(upper))
        )
        objective = augmentation_bound * lambda_scaled + sum(normalized)
        return self._solve(bounds + scalar_constraints, objective, deadline, threads)

    def run(self, max_points: int, time_limit: float, threads: int = 8,
            on_progress: Callable[[Point, int, float], None] | None = None):
        started = perf_counter()
        deadline = started + time_limit
        ideal, solves = self.compute_ideal(deadline, threads)
        archive = []
        bounds = [self.initial_upper]
        reason = "complete"
        active = None
        try:
            while bounds and len(archive) < max_points:
                if perf_counter() >= deadline:
                    reason = "time_limit"
                    break
                active = max(bounds, key=lambda u: self._priority(u, ideal))
                bounds.remove(active)
                point = self._solve_box(active, ideal, deadline, threads)
                solves += 1
                if point is None:
                    active = None
                    continue
                if point not in archive:
                    archive.append(point)
                bounds = update_upper_bounds(bounds + [active], point)
                active = None
                if on_progress:
                    on_progress(point, len(bounds), perf_counter() - started)
            if bounds and len(archive) >= max_points:
                reason = "point_limit"
        except TimeoutError:
            if active is not None:
                bounds.append(active)
            reason = "time_limit"
        return SearchResult(archive, bounds, ideal, not bounds, reason,
                            perf_counter() - started, solves)
