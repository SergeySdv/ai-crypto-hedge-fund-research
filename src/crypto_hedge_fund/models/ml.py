"""Classical walk-forward ML predictions for Level 2 validation."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


@dataclass(frozen=True)
class WalkForwardPrediction:
    """Prediction table and diagnostics for one model family."""

    model_name: str
    predictions: pd.DataFrame
    predictive_metrics: dict[str, float]
    fit_audit: pd.DataFrame


def walk_forward_ml_predictions(
    features: pd.DataFrame,
    *,
    feature_columns: tuple[str, ...],
    validation_mask: pd.Series,
    seeds: tuple[int, ...],
    min_train_samples: int = 120,
    refit_frequency: str = "monthly",
) -> list[WalkForwardPrediction]:
    """Fit Logistic Regression and HGB classifiers with causal expanding windows."""

    validation_rows = features.loc[validation_mask].copy()
    outputs: list[WalkForwardPrediction] = []
    for model_name in ("ml_logistic", "ml_hist_gradient_boosting"):
        prediction_frames: list[pd.DataFrame] = []
        audits: list[pd.DataFrame] = []
        for seed in seeds:
            preds, audit = _predict_one_seed(
                features,
                validation_rows=validation_rows,
                feature_columns=feature_columns,
                model_name=model_name,
                seed=seed,
                min_train_samples=min_train_samples,
                refit_frequency=refit_frequency,
            )
            preds["seed"] = seed
            prediction_frames.append(preds)
            audits.append(audit)
        predictions = pd.concat(prediction_frames, ignore_index=True)
        first_seed = predictions.loc[predictions["seed"] == seeds[0]].copy()
        metrics = predictive_metrics(first_seed["target_label"], first_seed["probability"])
        metrics["seed_count"] = float(len(seeds))
        outputs.append(
            WalkForwardPrediction(
                model_name=model_name,
                predictions=first_seed.drop(columns=["seed"]).reset_index(drop=True),
                predictive_metrics=metrics,
                fit_audit=pd.concat(audits, ignore_index=True),
            )
        )
    return outputs


def predictive_metrics(labels: pd.Series, probabilities: pd.Series) -> dict[str, float]:
    """Return predictive metrics separated from trading metrics."""

    y_true = labels.astype("int64").to_numpy()
    y_prob = probabilities.astype("float64").clip(1e-6, 1.0 - 1e-6).to_numpy()
    metrics = {
        "log_loss": float(log_loss(y_true, y_prob, labels=[0, 1])),
        "brier_score": float(brier_score_loss(y_true, y_prob)),
        "positive_rate": float(np.mean(y_true)),
    }
    if len(np.unique(y_true)) == 2:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        metrics["pr_auc"] = float(average_precision_score(y_true, y_prob))
    else:
        metrics["roc_auc"] = 0.5
        metrics["pr_auc"] = float(np.mean(y_true))
    predicted = y_prob >= 0.5
    true_positive = float(((predicted == 1) & (y_true == 1)).sum())
    predicted_positive = float(predicted.sum())
    actual_positive = float((y_true == 1).sum())
    metrics["precision_at_threshold"] = (
        true_positive / predicted_positive if predicted_positive else 0.0
    )
    metrics["recall_at_threshold"] = true_positive / actual_positive if actual_positive else 0.0
    calibration_bins = pd.qcut(pd.Series(y_prob), q=min(5, len(y_prob)), duplicates="drop")
    calibration = (
        pd.DataFrame({"label": y_true, "probability": y_prob, "bin": calibration_bins})
        .groupby("bin", observed=False)
        .agg(label=("label", "mean"), probability=("probability", "mean"))
    )
    metrics["calibration_mae"] = (
        float((calibration["label"] - calibration["probability"]).abs().mean())
        if not calibration.empty
        else 0.0
    )
    return metrics


def _predict_one_seed(
    features: pd.DataFrame,
    *,
    validation_rows: pd.DataFrame,
    feature_columns: tuple[str, ...],
    model_name: str,
    seed: int,
    min_train_samples: int,
    refit_frequency: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    for _, group in _validation_groups(validation_rows, frequency=refit_frequency):
        group = group.sort_values("execution_time", kind="mergesort")
        first_execution = pd.Timestamp(group["execution_time"].iloc[0])
        available = features.loc[features["label_observation_time"] < first_execution]
        available = available.dropna(subset=[*feature_columns, "target_label"])
        fit_cutoff = (
            pd.Timestamp(available["label_observation_time"].max())
            if not available.empty
            else pd.NaT
        )
        if len(available) < min_train_samples or available["target_label"].nunique() < 2:
            pipeline = None
            status = "abstain"
        else:
            pipeline = _pipeline(model_name, seed=seed)
            pipeline.fit(
                available.loc[:, feature_columns], available["target_label"].astype("int64")
            )
            status = "ok"
        for row in group.itertuples(index=False):
            execution_time = pd.Timestamp(row.execution_time)
            probability = 0.5
            if pipeline is not None:
                probability = float(
                    pipeline.predict_proba(pd.DataFrame([row._asdict()])[list(feature_columns)])[
                        0, 1
                    ]
                )
            rows.append(
                {
                    "bar_start_utc": pd.Timestamp(row.bar_start_utc),
                    "execution_time": execution_time,
                    "feature_cutoff": pd.Timestamp(row.feature_cutoff),
                    "fit_cutoff": fit_cutoff,
                    "probability": probability,
                    "score": float(max(-1.0, min(1.0, (probability - 0.5) * 2.0))),
                    "confidence": float(max(0.0, min(1.0, abs(probability - 0.5) * 2.0))),
                    "target_label": int(row.target_label),
                    "forward_return": float(row.forward_return),
                    "status": status,
                }
            )
            audits.append(
                {
                    "model": model_name,
                    "seed": seed,
                    "bar_start_utc": pd.Timestamp(row.bar_start_utc),
                    "execution_time": execution_time,
                    "fit_cutoff": fit_cutoff,
                    "train_samples": len(available),
                    "used_future_labels": bool(
                        not available.empty
                        and (available["label_observation_time"] >= execution_time).any()
                    ),
                    "status": status,
                    "refit_frequency": refit_frequency,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(audits)


def _validation_groups(
    validation_rows: pd.DataFrame, *, frequency: str
) -> list[tuple[object, pd.DataFrame]]:
    rows = validation_rows.copy()
    rows["execution_time"] = pd.to_datetime(rows["execution_time"], utc=True)
    if frequency in {"monthly", "default_retrain_monthly"}:
        return list(rows.groupby(rows["execution_time"].dt.strftime("%Y-%m"), sort=True))
    if frequency in {"daily", "daily_expanding_validation"}:
        return list(rows.groupby(rows["execution_time"], sort=True))
    msg = f"unsupported ML refit frequency: {frequency}"
    raise ValueError(msg)


def _pipeline(model_name: str, *, seed: int) -> Pipeline:
    if model_name == "ml_logistic":
        model = LogisticRegression(max_iter=500, random_state=seed, class_weight="balanced")
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", model),
            ]
        )
    if model_name == "ml_hist_gradient_boosting":
        model = HistGradientBoostingClassifier(
            max_iter=60,
            learning_rate=0.05,
            max_leaf_nodes=15,
            random_state=seed,
            l2_regularization=0.01,
        )
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("model", model),
            ]
        )
    msg = f"unsupported model_name: {model_name}"
    raise ValueError(msg)
