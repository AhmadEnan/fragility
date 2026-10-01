"""Replay the frozen classifiers on normalized, derived features."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .benchmark import design
from .models import fit_logistic, predict_logistic

DATA = Path(__file__).resolve().parents[2] / "data/derived"


def score(cohort):
    features = pd.read_parquet(DATA / f"{cohort}_features.parquet")
    frozen = json.loads((DATA / "models.json").read_text())
    scores = {}
    for name, specifications in frozen[cohort].items():
        specifications = specifications if cohort == "dev" else [specifications]
        p = np.full(len(features), np.nan)
        for spec in specifications:
            selected = (
                features.fold.eq(spec["fold"]).to_numpy()
                if cohort == "dev"
                else np.ones(len(features), bool)
            )
            matrix, _ = design(features.loc[selected], spec["features"], spec["stats"])
            model = {"coef": np.asarray(spec["coef"]), "intercept": spec["intercept"]}
            p[selected] = predict_logistic(model, matrix)
        assert np.isfinite(p).all()
        scores["p_" + name] = p
    return features, scores


def verify_refits():
    frozen = json.loads((DATA / "models.json").read_text())
    train = pd.read_parquet(DATA / "train_features.parquet")
    dev = pd.read_parquet(DATA / "dev_features.parquet")
    errors = {}
    for cohort, frame in [("test", train), ("dev", dev)]:
        for name, specifications in frozen[cohort].items():
            specifications = specifications if cohort == "dev" else [specifications]
            largest = 0.0
            for spec in specifications:
                selected = (
                    frame.fold.ne(spec["fold"]).to_numpy()
                    if cohort == "dev"
                    else np.ones(len(frame), bool)
                )
                matrix, _ = design(frame.loc[selected], spec["features"])
                fitted = fit_logistic(
                    matrix, frame.loc[selected, "Y_CAP_2S"].to_numpy(float)
                )
                # IRLS can stop at slightly different points after affine input normalization.
                old = predict_logistic(
                    {"coef": np.asarray(spec["coef"]), "intercept": spec["intercept"]},
                    matrix,
                )
                new = predict_logistic(fitted, matrix)
                largest = max(largest, float(np.max(np.abs(old - new))))
                np.testing.assert_allclose(old, new, rtol=0, atol=1e-7)
            errors[cohort + ":" + name] = largest
    return errors


if __name__ == "__main__":
    print(json.dumps(verify_refits(), indent=2))
