"""Optional licensed-data SOG parity check."""

import os
from pathlib import Path
import numpy as np
import pytest
from fragility.config import CANONICAL_CONFIG
from fragility.pff import load_pff_state
from fragility.sog import score_state, aggregate_cells


def test_canonical_real_state_sog_parity():
    """Verify numerical parity of SOG calculation on canonical World Cup match state.

    Tests GOLD001 best documented frame (Match 10505, Frame 70930) against canonical
    experiment records from EXP_SOG_GOLD20_CONFIRMATION_023 (cases/GOLD001.md):
      - State F_SOG == 3.5180
      - Top cell: #9 Harry Kane @ 0 deg, Q == 6.1950, rank 1/80, pct 1.000
      - Rank 2 cell: #9 Harry Kane @ 45 deg, Q == 5.2533, rank 2/80, pct 0.987
      - Rank 3 cell: #9 Harry Kane @ 315 deg, Q == 4.0727, rank 3/80, pct 0.975
    """
    pff_root = os.environ.get("PFF_DATA_ROOT")
    valid_root = pff_root if pff_root and Path(pff_root).exists() else None
    if not valid_root:
        pytest.skip(
            "PFF tracking data or frame cache not configured (set PFF_DATA_ROOT)"
        )

    try:
        state = load_pff_state(valid_root, 10505, 70930, focal_is_home=True)
    except FileNotFoundError:
        pytest.skip(f"Match 10505 not found under {valid_root}")

    df, F = score_state(state, CANONICAL_CONFIG)
    assert np.isclose(F, 3.5180, atol=1e-3)

    with pytest.raises(KeyError):
        load_pff_state(valid_root, 10505, -1, focal_is_home=True)

    cells = aggregate_cells(df)
    top_cell = cells.iloc[0]
    assert top_cell["jersey"] == "9"
    assert np.isclose(top_cell["direction_deg"], 0.0)
    assert np.isclose(top_cell["Q"], 6.1950, atol=1e-3)
    assert top_cell["rank"] == 1
    assert np.isclose(top_cell["percentile"], 1.0)

    second_cell = cells.iloc[1]
    assert second_cell["jersey"] == "9"
    assert np.isclose(second_cell["direction_deg"], 45.0)
    assert np.isclose(second_cell["Q"], 5.2533, atol=1e-3)

    third_cell = cells.iloc[2]
    assert third_cell["jersey"] == "9"
    assert np.isclose(third_cell["direction_deg"], 315.0)
    assert np.isclose(third_cell["Q"], 4.0727, atol=1e-3)
