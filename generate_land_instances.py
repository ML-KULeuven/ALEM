"""Generate reproducible land-conservation instances.

The output layout is compatible with ``runner.py`` and
``benchmark_land_lex.py``::

    <output>/grid/data_grid_<index>.csv
    <output>/thr/data_thr_<index>.csv
"""

import argparse
import json
import random
from pathlib import Path

import numpy as np

from utility.generator import generate_land_conservation_data


def parse_args():
    parser = argparse.ArgumentParser(description="Generate land-conservation instances")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--species", type=int, default=15)
    parser.add_argument("--instances", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261106)
    parser.add_argument("--initial-cost", type=int, default=3)
    parser.add_argument("--min-populations", type=int, default=2)
    parser.add_argument("--max-populations", type=int, default=4)
    parser.add_argument("--population-size", type=int, nargs="+", default=[50])
    parser.add_argument("--threshold-ratio", type=float, nargs="+", default=[0.3, 0.5, 0.7])
    parser.add_argument("--cities", type=int, default=5)
    parser.add_argument("--max-city-size", type=int, default=5)
    parser.add_argument("--lakes", type=int, default=5)
    parser.add_argument("--max-lake-radius", type=int, default=4)
    parser.add_argument("--forests", type=int, default=5)
    parser.add_argument("--max-forest-radius", type=int, default=5)
    return parser.parse_args()


def validate_args(args):
    positive = {
        "width": args.width,
        "height": args.height,
        "species": args.species,
        "instances": args.instances,
        "min_populations": args.min_populations,
        "max_populations": args.max_populations,
        "max_city_size": args.max_city_size,
        "max_lake_radius": args.max_lake_radius,
        "max_forest_radius": args.max_forest_radius,
    }
    invalid = [name for name, value in positive.items() if value < 1]
    if invalid:
        raise ValueError(f"Expected positive values for: {', '.join(invalid)}")
    if args.min_populations > args.max_populations:
        raise ValueError("--min-populations cannot exceed --max-populations")
    if not all(0 < ratio <= 1 for ratio in args.threshold_ratio):
        raise ValueError("Threshold ratios must be in (0, 1]")


def main():
    args = parse_args()
    validate_args(args)
    grid_dir = args.output / "grid"
    threshold_dir = args.output / "thr"
    grid_dir.mkdir(parents=True, exist_ok=True)
    threshold_dir.mkdir(parents=True, exist_ok=True)

    generated = []
    for index in range(args.instances):
        instance_seed = args.seed + index
        random.seed(instance_seed)
        np.random.seed(instance_seed)
        grid = generate_land_conservation_data(
            width=args.width,
            height=args.height,
            initial_cost=args.initial_cost,
            animals=args.species,
            range_population=range(args.min_populations, args.max_populations + 1),
            set_population=args.population_size,
            set_threshold=args.threshold_ratio,
            cities=args.cities,
            max_size_cities=args.max_city_size,
            lakes=args.lakes,
            max_radius_lake=args.max_lake_radius,
            forests=args.forests,
            max_radius_forest=args.max_forest_radius,
        )
        grid_frame, threshold_frame = grid.convert_into_dfs()
        grid_frame.to_csv(grid_dir / f"data_grid_{index}.csv", index=False)
        threshold_frame.to_csv(threshold_dir / f"data_thr_{index}.csv", index=False)
        generated.append({"index": index, "seed": instance_seed})

    metadata = {
        "width": args.width,
        "height": args.height,
        "cells": args.width * args.height,
        "species": args.species,
        "instances": generated,
        "generator_parameters": {
            "initial_cost": args.initial_cost,
            "populations_per_species": [args.min_populations, args.max_populations],
            "population_size": args.population_size,
            "threshold_ratio": args.threshold_ratio,
            "cities": args.cities,
            "max_city_size": args.max_city_size,
            "lakes": args.lakes,
            "max_lake_radius": args.max_lake_radius,
            "forests": args.forests,
            "max_forest_radius": args.max_forest_radius,
        },
    }
    with (args.output / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
