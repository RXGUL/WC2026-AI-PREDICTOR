from pathlib import Path
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parent

STEPS = [
    "src/06_elo_ratings.py",
    "src/07_form_index.py",
    "src/08_head_to_head.py",
    "src/09_build_feature_table.py",
]


def run_step(script_path: str) -> float:
    start_time = time.perf_counter()
    print(f"\nRunning {script_path}...")

    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / script_path)],
        cwd=PROJECT_ROOT,
        check=True,
    )

    elapsed = time.perf_counter() - start_time
    print(f"Finished {script_path} in {elapsed:.2f}s")
    return elapsed


def main() -> None:
    total_start = time.perf_counter()
    timings = []

    for script_path in STEPS:
        timings.append((script_path, run_step(script_path)))

    total_elapsed = time.perf_counter() - total_start

    print("\nDay 2 pipeline timings")
    print("-" * 40)
    for script_path, elapsed in timings:
        print(f"{script_path:<30} {elapsed:>7.2f}s")
    print("-" * 40)
    print(f"{'Total':<30} {total_elapsed:>7.2f}s")


if __name__ == "__main__":
    main()
