from pathlib import Path
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parent

STEPS = [
    "src/11_train_xgboost.py",
    "src/12_giant_killer.py",
    "src/13_shap_explainability.py",
    "src/14_monte_carlo.py",
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

    print("\nDay 3 pipeline timings")
    print("-" * 42)
    for script_path, elapsed in timings:
        print(f"{script_path:<32} {elapsed:>7.2f}s")
    print("-" * 42)
    print(f"{'Total':<32} {total_elapsed:>7.2f}s")


if __name__ == "__main__":
    main()
