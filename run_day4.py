from pathlib import Path
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parent
REPORT_SCRIPT = "src/15_generate_reports.py"


def main() -> None:
    start_time = time.perf_counter()
    print(f"\nRunning {REPORT_SCRIPT}...")

    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / REPORT_SCRIPT)],
        cwd=PROJECT_ROOT,
        check=True,
    )

    elapsed = time.perf_counter() - start_time

    print("\nDay 4 report generation timing")
    print("-" * 42)
    print(f"{REPORT_SCRIPT:<32} {elapsed:>7.2f}s")
    print("-" * 42)
    print(f"{'Total':<32} {elapsed:>7.2f}s")


if __name__ == "__main__":
    main()
