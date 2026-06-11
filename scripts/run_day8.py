from pathlib import Path
import os
import subprocess
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parent
UPLOAD_SCRIPT = "src/18_supabase_uploader.py"


def main() -> None:
    start_time = time.perf_counter()
    print(f"\nRunning {UPLOAD_SCRIPT}...", flush=True)
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / UPLOAD_SCRIPT)],
        cwd=PROJECT_ROOT,
        env=env,
        check=True,
    )

    elapsed = time.perf_counter() - start_time

    print("\nDay 8 Supabase upload timing")
    print("-" * 42)
    print(f"{UPLOAD_SCRIPT:<32} {elapsed:>7.2f}s")
    print("-" * 42)
    print(f"{'Total':<32} {elapsed:>7.2f}s")


if __name__ == "__main__":
    main()
