"""Maintainer-only source export. Reads the research checkout; never imports it.

The released package does not require this script or the research checkout.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil

DEST = Path(__file__).resolve().parents[1]
RECORDS = []


def extract(root, source, target, names, header):
    p = root / source
    text = p.read_text(encoding="utf-8-sig")
    nodes = {n.name: n for n in ast.parse(text).body
             if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    parts = [header]
    for name in names:
        n = nodes[name]
        parts.append(ast.get_source_segment(text, n))
        RECORDS.append({"source": source, "target": target, "symbol": name,
                        "source_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                        "ast_sha256": hashlib.sha256(ast.dump(n, include_attributes=False).encode()).hexdigest()})
    out = DEST / target
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n\n".join(parts) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("research_root", type=Path)
    root = ap.parse_args().research_root.resolve()
    for p in sorted((root / "src/obso").glob("*.py")):
        out = DEST / "src/obso" / p.name
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, out)
        RECORDS.append({"source": str(p.relative_to(root)).replace("\\", "/"),
                        "target": str(out.relative_to(DEST)).replace("\\", "/"),
                        "source_sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    extract(root, "src/fragility/passes.py", "src/fragility/raw_events.py",
            ["load_events", "assign_possessions", "add_frame_timing"],
            '''"""Frozen event parsing and possession segmentation; no historical outcome proxy."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
BREAK_EVENTS = frozenset({"OUT", "SUB", "END", "G", "ON", "OFF"})
KICKOFF_EVENTS = frozenset({"FIRSTKICKOFF", "SECONDKICKOFF", "THIRDKICKOFF", "FOURTHKICKOFF"})
FPS = 29.97''')
    extract(root, "scripts/obso_pilot/00_build_event_frame_index.py", "src/fragility/raw_index.py",
            ["build"], '''"""Original raw tracking-to-event index builder."""
import bz2
import json
from pathlib import Path
import numpy as np
import pandas as pd''')
    cap_header = '''"""Frozen CAP labels and tracking annotation with portable, explicit input paths.

Call configure before reading. Inputs are read-only; no work occurs on import.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .raw_io import load_cache, load_index, event_table
from . import raw_events
RAW_FPS_DEFAULT = 29.97
CACHE_STRIDE = 8
PHASE_TRANSITION_MAX_S = 5.0
SLOT_CHANGE_GUARD_FRAMES = 3
CONTROL_RETENTION_S = 1.0
ADVANTAGE_WINDOW_S = 2.0
PROGRESS_PRIMARY_M = 5.0
PROGRESS_SENSITIVITY_M = (3.0, 8.0)
BOUNDARY_AMBIGUOUS_M = 0.50
BOX_X = 52.5 - 16.5
BOX_Y = 20.16 / 2.0
SYNC_MAX_RAW_FRAMES = 32
FAMILY_PASS, FAMILY_CROSS, FAMILY_CARRY = "pass", "cross", "carry"
PASS_LIKE = (FAMILY_PASS, FAMILY_CROSS)
THIRD_EDGES = [(-52.5, -17.5, "defensive"), (-17.5, 17.5, "middle"), (17.5, 52.5, "attacking")]
META_DIR = EVENT_DIR = None
_FPS_CACHE, _EXTRA_CACHE, _EV_CACHE, _ANNOT_CACHE = {}, {}, {}, {}
_UNIQUE_CACHE, _DUP_COUNTS, _VIEW_CACHE = {}, {}, {}

def configure(raw_root, cache_root, index_root):
    from . import raw_io
    global META_DIR, EVENT_DIR
    raw_io.configure(raw_root, cache_root, index_root)
    META_DIR, EVENT_DIR = Path(raw_root) / "Metadata", Path(raw_root) / "Event Data"
    for cache in (_FPS_CACHE, _EXTRA_CACHE, _EV_CACHE, _ANNOT_CACHE, _UNIQUE_CACHE, _DUP_COUNTS, _VIEW_CACHE):
        cache.clear()

def passes_module():
    return raw_events'''
    extract(root, "scripts/fragility_operator_pilot/op_common.py", "src/fragility/raw_third.py",
            ["third_of"], 'THIRD_EDGES = [(-52.5, -17.5, "defensive"), (-17.5, 17.5, "middle"), (17.5, 52.5, "attacking")]')
    cap_header += "\nfrom .raw_third import third_of"
    extract(root, "scripts/cap_validation_pilot/cap_common.py", "src/fragility/raw_cap.py",
            ["match_fps", "_extra_outcome_fields", "events_with_possessions", "possession_table",
             "frame_possession", "load_cache_unique", "corrected_annotation", "state_phase",
             "TrackingView", "view", "detect_units", "_family_and_completion", "candidate_actions", "label_cap"], cap_header)
    extract(root, "scripts/exp022_res0_predictive_pilot/e22_common.py", "src/fragility/raw_cohort.py",
            ["eligible_frames", "cadence_states", "cap_events", "label_states", "assign_folds"],
            '''"""Original frozen eligibility, cadence, release labels and match-grouped folds."""
import numpy as np
import pandas as pd
from . import raw_cap as cc
CAP_PHASE_REQUIRED = "settled"
CAP_SYNC_MAX_RAW_FRAMES = 32
CADENCE_S = 1.0
N_FOLDS = 5''')
    extract(root, "scripts/exp022_res0_predictive_pilot/e22_solver.py", "src/fragility/fast_sog.py",
            ["_step_table", "_integrate_from_player", "solve_state_res0", "state_scores_res0"],
            '''"""Original frozen-equivalent SOG solver; arithmetic hoisting only, no formula changes."""
import numpy as np
from .research_operator import SPEC, StructuralOperator
from obso.state import offside_line
from obso.ppcf import time_to_intercept
COLLISION_RADIUS_M = 0.5
INTEGRATION_CHUNK = 4
HALF_LEN, HALF_WID = 52.5, 34.0''')
    extract(root, "scripts/exp032_literature_benchmark/01_comparators.py", "src/fragility/das_adapter.py",
            ["_das_batch", "_frozen_cell_area"],
            '''"""Frozen EXP032 AM03 DAS call and exact grid-area expression."""
import json
from pathlib import Path
CFG = json.loads((Path(__file__).resolve().parents[2] / "configs/literature_benchmark.json").read_text())''')
    extract(root, "scripts/exp025_sog_path_accessibility/04_score.py", "src/fragility/tactical_summary.py",
            ["dir6", "run_stats", "summarize"],
            '''"""Frozen tactical temporal recovery summaries (EXP023/024 convention)."""
import numpy as np
import pandas as pd
VENDOR_FPS = 29.9697
DT_STATE = 8.0 / VENDOR_FPS''')
    for src, dst in [
        ("configs/exp032_literature_benchmark.json", "configs/literature_benchmark.json"),
        ("assets/EPV_grid.csv", "assets/EPV_grid.csv"),
        ("experiments/EXP_SOG_PREDICTIVE_CONFIRM_029/cohorts/TEST_WINDOW_EXCLUSIONS.csv", "data/identity/test_window_exclusions.csv"),
        ("experiments/EXP_SOG_GOLD20_CONFIRMATION_023/01_CASE_ALIGNMENT_FREEZE.csv", "data/validation/case_alignment_freeze.csv"),
        ("experiments/EXP_SOG_GOLD20_CONFIRMATION_023/02_PLAYER_ACTION_FREEZE.csv", "data/validation/player_action_freeze.csv"),
        ("experiments/EXP_SOG_INCREMENTAL_ABLATION_024/DOCUMENTED_ACTION_COMPARISON.csv", "data/validation/action_recovery_reference.csv"),
        ("experiments/EXP_SOG_INCREMENTAL_ABLATION_024/PREREGISTRATION.md", "docs/protocols/tactical_ablation.md"),
        ("experiments/EXP_SOG_PREDICTIVE_CONFIRM_029/PREREGISTRATION.md", "docs/protocols/heldout.md"),
        ("docs/submission/ssac27_2026-09-30/ABSTRACT.md", "docs/submission/ABSTRACT.md"),
        ("docs/submission/ssac27_2026-09-30/FIGURE_CAPTIONS.md", "docs/submission/FIGURE_CAPTIONS.md"),
        ("docs/submission/ssac27_2026-09-30/CLAIMS_AND_PROVENANCE.md", "docs/submission/CLAIMS_AND_PROVENANCE.md"),
    ]:
        out = DEST / dst
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / src, out)
        RECORDS.append({"source": src, "target": dst, "source_sha256": hashlib.sha256((root/src).read_bytes()).hexdigest()})
    (DEST / "results/source_export_manifest.json").write_text(json.dumps(RECORDS, indent=2) + "\n")


if __name__ == "__main__":
    main()
