"""Bounded four-objective box search for the land-conservation model.

This command always requires a finite point limit and therefore never requests
unbounded Pareto-front enumeration.
"""

import argparse
import json
from pathlib import Path
from time import perf_counter

from enumerating_methods.box_search_ortools import IntegerBoxSearchORTools
from problems.land_conservation_problem import LandConModel
from utility.grid_class import Grid


def scalar(expression):
    try:
        if expression.size == 1:
            return expression.item()
    except (AttributeError, TypeError):
        pass
    return expression


def parse_args():
    parser = argparse.ArgumentParser(description="Bounded four-objective land box search")
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--index", type=int, default=0)
    parser.add_argument("--species-limit", type=int,
                        help="Use only the first N species and matching thresholds")
    parser.add_argument("--max-points", type=int, required=True)
    parser.add_argument("--time-limit", type=float, default=2 * 60 * 60,
                        help="Total search limit in seconds (default: 7200 / 2 hours)")
    parser.add_argument("--threads", type=int, default=8)
    parser.add_argument("--backend", choices=["ortools"], default="ortools")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.threads != 8:
        raise ValueError("Coverage enumeration is configured to use exactly 8 OR-Tools workers")
    started = perf_counter()
    grid = Grid(path_grid=args.folder / "grid" / f"data_grid_{args.index}.csv",
                path_threshold=args.folder / "thr" / f"data_thr_{args.index}.csv",
                compute_distances=False)
    source_species = grid.animals
    if args.species_limit is not None:
        if not 1 <= args.species_limit <= source_species:
            raise ValueError(f"species limit must be in [1, {source_species}]")
        grid.animals = args.species_limit
        grid.grid_species = grid.grid_species[:args.species_limit]
        grid.species_threshold = grid.species_threshold[:args.species_limit]
    model, variables, names, _ = LandConModel(grid, 4, "extrema").make_model()
    expressions = [scalar(variables[name]) for name in names]
    lower = [int(expression.lb) for expression in expressions]
    upper = [int(expression.ub) for expression in expressions]

    def progress(point, boxes, elapsed):
        print(json.dumps({"point": point, "remaining_upper_bounds": boxes,
                          "elapsed_seconds": elapsed}), flush=True)

    search = IntegerBoxSearchORTools(model, expressions, lower, upper)
    result = search.run(max_points=args.max_points, time_limit=args.time_limit,
                        threads=args.threads, on_progress=progress)
    payload = {
        "instance": str(args.folder), "index": args.index,
        "grid": [int(grid.height), int(grid.width)], "cells": int(grid.height * grid.width),
        "species": int(grid.animals), "source_species": int(source_species),
        "backend": args.backend,
        "objective_names": names,
        "ideal": result.ideal, "points": result.points,
        "point_count": len(result.points),
        "remaining_upper_bounds": result.upper_bounds,
        "remaining_upper_bound_count": len(result.upper_bounds),
        "complete": result.complete, "stop_reason": result.stop_reason,
        "search_seconds": result.elapsed_seconds, "total_seconds": perf_counter() - started,
        "solver_calls": result.solves,
    }
    rendered = json.dumps(payload, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
