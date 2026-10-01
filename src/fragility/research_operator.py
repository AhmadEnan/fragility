"""Minimal frozen operator initialization used by the exported fast solver.

The initialization is expression-identical to sfa_common.StructuralOperator.
Historical structural-score experiments are deliberately outside this package.
"""
import numpy as np
from obso import DangerConfig, canonical_params, make_grid
from obso.fieldvalue import field_value_surface
from obso.operator import OperatorSpec, StateOperator

GRID = make_grid()
CONFIG = DangerConfig()
CANONICAL = canonical_params()
FIELD_VALUE = field_value_surface(GRID)
SPEC = OperatorSpec()


class StructuralOperator:
    def __init__(self, state, spec=SPEC):
        self.state = state
        self.spec = spec
        self.op = StateOperator(state, CANONICAL, CONFIG, GRID, FIELD_VALUE, spec)
        self.base = self.op.baseline()
        self.A_base = self.base.transition * np.clip(self.base.control, 0.0, 1.0)
        self.S = self.base.score
        self.W = self.base.field_value
        self.n_cells = self.A_base.size
