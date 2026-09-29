"""Self-verification script for notebooks/reproduce_ssac27.ipynb in CI."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
nb_path = REPO_ROOT / "notebooks" / "reproduce_ssac27.ipynb"

assert nb_path.exists(), f"Notebook not found at {nb_path}"
with open(nb_path, encoding="utf-8") as f:
    nb = json.load(f)

code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
assert len(code_cells) <= 10, f"Too many code cells: {len(code_cells)} (budget <= 10)"

g = {"__file__": str(nb_path)}
for idx, cell in enumerate(code_cells, 1):
    code = "".join(cell["source"])
    print(f"Executing notebook code cell {idx}...")
    exec(code, g)

print("SSAC27 Notebook Reproduction Verified successfully!")
