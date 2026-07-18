"""Architecture tests for the standalone dashboard data boundary."""

import ast
from pathlib import Path


DASHBOARD_DIRECTORY = Path(__file__).resolve().parents[1] / "dashboard"


def test_dashboard_package_has_no_database_imports():
    """The Streamlit layer must consume Parquet rather than the SQLite DAO."""
    forbidden_prefixes = ("sqlite3", "strava_data.db")
    violations = []

    for source_path in DASHBOARD_DIRECTORY.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                imported_names = [node.module or ""]
            else:
                continue
            for imported_name in imported_names:
                if imported_name.startswith(forbidden_prefixes):
                    violations.append(f"{source_path.name}: {imported_name}")

    assert not violations, "Dashboard contains database imports: " + ", ".join(violations)
