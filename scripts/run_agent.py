from pathlib import Path
import os
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
AGENT_SCRIPT = PROJECT_ROOT / "src" / "17_agent.py"


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    load_env(PROJECT_ROOT / ".env")
    os.environ["SCAN_INTERVAL_SECONDS"] = "60"

    print(
        "WC2026 Agent starting...\n"
        "Scanning 48 teams every 6 hours\n"
        "Press Ctrl+C to stop"
    )

    subprocess.run(
        [sys.executable, str(AGENT_SCRIPT)],
        cwd=PROJECT_ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
