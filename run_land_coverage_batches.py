"""Run the coverage/box anytime enumerator sequentially for one instance batch."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from time import perf_counter


BATCHES = {
    "0-2": range(0, 3),
    "3-5": range(3, 6),
    "6-7": range(6, 8),
    "8-9": range(8, 10),
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run four-objective coverage enumeration sequentially for a batch")
    parser.add_argument("--batch", choices=BATCHES, required=True)
    parser.add_argument(
        "--folder", type=Path,
        default=Path("data/land_conservation_scaling/20x20_15sp_10inst"))
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("results/coverage_20x20_15sp_4obj_2h"))
    parser.add_argument("--dry-run", action="store_true",
                        help="Print commands without starting enumeration")
    return parser.parse_args()


def main():
    args = parse_args()
    timeout_seconds = 2 * 60 * 60
    threads = 8
    args.output_dir.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update({
        "OMP_NUM_THREADS": str(threads),
        "MKL_NUM_THREADS": str(threads),
        "OPENBLAS_NUM_THREADS": str(threads),
    })
    summary = []

    for index in BATCHES[args.batch]:
        output = args.output_dir / f"instance_{index}.json"
        log = args.output_dir / f"instance_{index}.log"
        command = [
            sys.executable, "-u", "benchmark_land_boxes.py",
            "--folder", str(args.folder),
            "--index", str(index),
            "--species-limit", "15",
            "--backend", "ortools",
            "--max-points", "1000000",
            "--time-limit", str(timeout_seconds),
            "--threads", str(threads),
            "--output", str(output),
        ]
        print(f"Starting coverage enumeration for instance {index}; log={log}", flush=True)
        if args.dry_run:
            print(" ".join(command), flush=True)
            continue

        started = perf_counter()
        with log.open("w", encoding="utf-8") as handle:
            process = subprocess.run(
                command, stdout=handle, stderr=subprocess.STDOUT, env=environment)
        record = {
            "instance": index,
            "returncode": process.returncode,
            "wall_seconds": perf_counter() - started,
            "result": str(output),
            "log": str(log),
        }
        if output.exists():
            result = json.loads(output.read_text(encoding="utf-8"))
            record.update({
                "points": result["point_count"],
                "complete": result["complete"],
                "stop_reason": result["stop_reason"],
                "remaining_upper_bounds": result["remaining_upper_bound_count"],
            })
        summary.append(record)
        print(json.dumps(record), flush=True)

    if args.dry_run:
        return
    summary_path = args.output_dir / f"batch_{args.batch}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if any(record["returncode"] != 0 for record in summary):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
