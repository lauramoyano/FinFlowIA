"""Script to run Alembic database migrations."""

import subprocess
import sys
from pathlib import Path


def run_migrations(revision: str = "head") -> int:
    """Run Alembic migrations to the specified revision."""
    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        ["alembic", "upgrade", revision],
        cwd=str(project_root),
        capture_output=False,
    )
    return result.returncode


if __name__ == "__main__":
    revision = sys.argv[1] if len(sys.argv) > 1 else "head"
    print(f"Running migrations to revision: {revision}")
    exit_code = run_migrations(revision)
    if exit_code == 0:
        print("Migrations completed successfully!")
    else:
        print("Migration failed!")
    sys.exit(exit_code)
