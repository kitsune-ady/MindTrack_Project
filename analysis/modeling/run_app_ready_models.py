"""Compare depression models on fields proposed for the mobile app.

Field selection is trained inside each CV fold. It groups one-hot encoded
L1 logistic-regression coefficients back to original questionnaire fields,
selects fields at or above the median nonzero score, and always keeps the
recalculated TMD total. The holdout evaluates only the CV-selected model.
"""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score,
    balanced_accuracy_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score)
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.class_weight import compute_sample_weight

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data/processed/depression_analysis_dataset.csv"
TRAIN_SPLIT = ROOT / "data/splits/depression_train_80pct.csv"
TEST_SPLIT = ROOT / "data/splits/depression_test_20pct.csv"
RESULTS, MODELS = ROOT / "results", ROOT / "models"
SEED, THRESHOLD = 42, 0.50
TARGET, ID = "Higher_Beck_Score_11plus", "Code"
ALWAYS_KEEP = ("TMD_Total_Recomputed",)
# Average_Time_Use is excluded: only one student is in its 1-3 hour category.
NOMINAL = ["Department", "Sex", "MS", "SES", "Living_Arrangement", "Residence_Area",
           "Subscription_Plan", "Network _Access", "Areas_Use", "Type_MD"]
NUMERIC = ["Age", "Semester", "Family_Expression", "Family_Activities", "Mobile_Use_Rules",
           "Phone_Discrimination", "Phone_Related_Arguments", "Time_First_Cellphone",
           "TMD_Total_Recomputed"]
APP_FLAGS = ["Using_Text Messaging_Apps", "Using_Games_Apps", "Using_social media_Apps",
             "Using_Music_Apps", "Using_Videos_Apps", "Using_Ttime-management_Apps",
             "Using_Camara_Apps", "Using_Mail_Apps"]
FEATURES = NOMINAL + NUMERIC + APP_FLAGS


def make_preprocessor(columns):
    nominal = [c for c in columns if c in NOMINAL]
    numeric = [c for c in columns if c in NUMERIC + APP_FLAGS]
    transforms = []
    if numeric:
        transforms.append(("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numeric))
    if nominal:
        try:
            encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
        except TypeError:
            encoder = OneHotEncoder(handle_unknown="ignore", sparse=False)
        transforms.append(("categorical", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", encoder),
        ]), nominal))
    return ColumnTransformer(transforms, remainder="drop", verbose_feature_names_out=True)


class AppFieldSelector(BaseEstimator, TransformerMixin):
    """Select raw form fields and preprocess them within each training fold."""
    def __init__(self, select_fields=False, always_keep=ALWAYS_KEEP):
        self.select_fields = select_fields
        self.always_keep = always_keep

    def fit(self, X, y):
        missing = [c for c in FEATURES if c not in X.columns]
        if missing:
            raise ValueError(f"Missing app candidate fields: {missing}")
        self.feature_scores_ = {c: 0.0 for c in FEATURES}
        if self.select_fields:
            pre = make_preprocessor(FEATURES)
            encoded = pre.fit_transform(X[FEATURES], y)
            selector = LogisticRegression(l1_ratio=1, C=0.25, solver="liblinear",
                class_weight="balanced", max_iter=3000, random_state=SEED)
            selector.fit(encoded, y)
            for name, coef in zip(pre.get_feature_names_out(), np.abs(selector.coef_[0])):
                self.feature_scores_[self._source_field(name)] += float(coef)
            positive = [score for score in self.feature_scores_.values() if score > 0]
            if positive:
                cutoff = float(np.median(positive))
                chosen = [c for c, score in self.feature_scores_.items()
                          if score > 0 and score >= cutoff]
            else:
                chosen = sorted(FEATURES, key=lambda c: (-self.feature_scores_[c], c))[:5]
            chosen = set(chosen) | set(self.always_keep)
            self.selected_fields_ = [c for c in FEATURES if c in chosen]
        else:
            self.selected_fields_ = FEATURES.copy()
        self.preprocessor_ = make_preprocessor(self.selected_fields_)
        self.preprocessor_.fit(X[self.selected_fields_], y)
        self.encoded_feature_names_ = self.preprocessor_.get_feature_names_out()
        return self

    @staticmethod
    def _source_field(encoded_name):
        name = str(encoded_name)
        for column in NOMINAL:
            if name.startswith(f"categorical__{column}_") or name == f"categorical__{column}":
                return column
        for column in NUMERIC + APP_FLAGS:
            if name == f"numeric__{column}":
                return column
        raise ValueError(f"Cannot map encoded feature back to app field: {name}")

    def transform(self, X):
        missing = [c for c in self.selected_fields_ if c not in X.columns]
        if missing:
            raise ValueError(f"Missing selected app fields at prediction time: {missing}")
        return self.preprocessor_.transform(X[self.selected_fields_])

    def get_feature_names_out(self, input_features=None):
        return self.encoded_feature_names_


def model_specs():
    return {
        "Baseline (most common)": DummyClassifier(strategy="most_frequent"),
        "Logistic regression": LogisticRegression(max_iter=3000, solver="liblinear", random_state=SEED),
        "Decision tree": DecisionTreeClassifier(max_depth=5, min_samples_leaf=10, random_state=SEED),
        "Random forest": RandomForestClassifier(n_estimators=400, max_features="sqrt",
            min_samples_leaf=4, n_jobs=-1, random_state=SEED),
        "Gradient boosting": GradientBoostingClassifier(n_estimators=150, learning_rate=0.05,
            max_depth=2, min_samples_leaf=10, random_state=SEED),
    }


def make_pipeline(estimator, select_fields):
    return Pipeline([("app_fields", AppFieldSelector(select_fields=select_fields)),
                     ("scale_encoded", StandardScaler()), ("model", estimator)])


def get_saved_split(data):
    train_ids = pd.read_csv(TRAIN_SPLIT, dtype={ID: "string"})[[ID, TARGET]]
    test_ids = pd.read_csv(TEST_SPLIT, dtype={ID: "string"})[[ID, TARGET]]
    if set(train_ids[ID]) & set(test_ids[ID]):
        raise ValueError("Saved training and test sets overlap")
    indexed = data.assign(**{ID: data[ID].astype("string")}).set_index(ID, drop=False)
    train, test = indexed.loc[train_ids[ID].tolist()], indexed.loc[test_ids[ID].tolist()]
    for label, rows, split in (("training", train, train_ids), ("test", test, test_ids)):
        if not np.array_equal(rows[TARGET].to_numpy(), split[TARGET].to_numpy()):
            raise ValueError(f"Saved {label} labels do not match the analysis dataset")
    if len(train) + len(test) != len(data):
        raise ValueError("Saved splits do not cover the prepared dataset")
    return train, test


def test_metrics(y, probability):
    predicted = (probability >= THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, predicted, labels=[0, 1]).ravel()
    return {
        "test_accuracy": accuracy_score(y, predicted),
        "test_precision": precision_score(y, predicted, zero_division=0),
        "test_recall": recall_score(y, predicted, zero_division=0),
        "test_f1": f1_score(y, predicted, zero_division=0),
        "test_balanced_accuracy": balanced_accuracy_score(y, predicted),
        "test_roc_auc": roc_auc_score(y, probability),
        "test_pr_auc": average_precision_score(y, probability),
        "test_tn": int(tn), "test_fp": int(fp), "test_fn": int(fn), "test_tp": int(tp),
    }


def main():
    RESULTS.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(parents=True, exist_ok=True)
    data = pd.read_csv(DATA_PATH, dtype={ID: "string"})
    required = FEATURES + [ID, TARGET, "Beck_Total"]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(f"Prepared dataset is missing fields: {missing}")
    if data[FEATURES + [TARGET]].isna().any().any():
        raise ValueError("App inputs or target contain missing values")

    X = data[FEATURES].copy()
    # The source dictionary uses 1=No and 2=Yes for app flags.
    for column in APP_FLAGS:
        values = set(pd.to_numeric(X[column], errors="raise").unique())
        if not values.issubset({1, 2}):
            raise ValueError(f"Unexpected codes in {column}: {values}")
        X[column] = X[column].map({1: 0, 2: 1})
    y = data[TARGET].astype(int)
    X.index = data[ID].astype("string")
    y.index = data[ID].astype("string")
    train, test = get_saved_split(data)
    X_train, y_train = X.loc[train.index], y.loc[train.index]
    X_test, y_test = X.loc[test.index], y.loc[test.index]

    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
    folds = list(cv.split(X_train, y_train))
    rows, candidates = [], []
    for model_name, estimator in model_specs().items():
        variants = [("Full app fields", False)] if model_name.startswith("Baseline") else [
            ("Full app fields", False), ("L1-selected app fields", True)]
        for input_set, select_fields in variants:
            pipeline = estimator if model_name.startswith("Baseline") else make_pipeline(estimator, select_fields)
            for fold, (fit_i, valid_i) in enumerate(folds, start=1):
                fitted = clone(pipeline)
                X_fit, X_valid = X_train.iloc[fit_i], X_train.iloc[valid_i]
                y_fit, y_valid = y_train.iloc[fit_i], y_train.iloc[valid_i]
                if model_name.startswith("Baseline"):
                    fitted.fit(X_fit, y_fit)
                else:
                    fitted.fit(X_fit, y_fit,
                        model__sample_weight=compute_sample_weight("balanced", y_fit))
                probability = fitted.predict_proba(X_valid)[:, 1]
                rows.append({
                    "model": model_name, "input_set": input_set, "fold": fold,
                    "cv_pr_auc": average_precision_score(y_valid, probability),
                    "cv_roc_auc": roc_auc_score(y_valid, probability),
                    "cv_balanced_accuracy_at_0_50": balanced_accuracy_score(
                        y_valid, (probability >= THRESHOLD).astype(int)),
                })
            if not model_name.startswith("Baseline"):
                candidates.append((model_name, input_set, pipeline))

    fold_results = pd.DataFrame(rows)
    summary = fold_results.groupby(["model", "input_set"], as_index=False).agg(
        cv_pr_auc_mean=("cv_pr_auc", "mean"), cv_pr_auc_sd=("cv_pr_auc", "std"),
        cv_roc_auc_mean=("cv_roc_auc", "mean"), cv_roc_auc_sd=("cv_roc_auc", "std"),
        cv_balanced_accuracy_mean=("cv_balanced_accuracy_at_0_50", "mean"))
    winner = summary[summary.model != "Baseline (most common)"].sort_values(
        "cv_pr_auc_mean", ascending=False).iloc[0]
    winner_name, winner_inputs = winner.model, winner.input_set
    winner_pipeline = next(p for name, fields, p in candidates
                          if name == winner_name and fields == winner_inputs)

    # Select the best compact model using training CV only. Both the overall
    # CV winner and best L1-reduced candidate are evaluated for reporting; the
    # holdout has previously been viewed, so both test estimates are preliminary.
    compact_rows = summary[summary.input_set == "L1-selected app fields"].sort_values(
        "cv_pr_auc_mean", ascending=False)
    compact_name = compact_rows.iloc[0].model
    compact_inputs = "L1-selected app fields"
    compact_pipeline = next(p for name, fields, p in candidates
                           if name == compact_name and fields == compact_inputs)

    def fit_candidate(pipeline):
        fitted = clone(pipeline)
        fitted.fit(X_train, y_train,
            model__sample_weight=compute_sample_weight("balanced", y_train))
        return fitted

    best = fit_candidate(winner_pipeline)
    compact_best = fit_candidate(compact_pipeline)
    probability = best.predict_proba(X_test)[:, 1]
    compact_probability = compact_best.predict_proba(X_test)[:, 1]
    chosen = (summary.model == winner_name) & (summary.input_set == winner_inputs)
    compact_chosen = (summary.model == compact_name) & (summary.input_set == compact_inputs)
    summary["selected_for_test"] = chosen
    summary["selected_compact_for_test"] = compact_chosen
    for metric, value in test_metrics(y_test, probability).items():
        summary[metric] = np.nan
        summary.loc[chosen, metric] = value
    compact_metrics = test_metrics(y_test, compact_probability)
    for metric, value in compact_metrics.items():
        summary.loc[compact_chosen, metric] = value
    summary["test_threshold"] = np.where(chosen | compact_chosen, THRESHOLD, np.nan)
    summary.to_csv(RESULTS / "app_ready_model_comparison.csv", index=False)
    fold_results.to_csv(RESULTS / "app_ready_repeated_cv_folds.csv", index=False)

    deployed_selector = best.named_steps["app_fields"]
    deployed_fields = deployed_selector.selected_fields_
    compact_fields = compact_best.named_steps["app_fields"].selected_fields_

    # Fit a separate selector on the training split only, so the compact
    # candidate list is available even when the full-input model wins.
    l1_selector = AppFieldSelector(select_fields=True).fit(X_train, y_train)
    l1_fields = l1_selector.selected_fields_
    pd.DataFrame([{
        "field": field,
        "selection_score_abs_l1_coefficient_sum": l1_selector.feature_scores_[field],
        "selected_by_l1": field in l1_fields,
        "always_keep": field in ALWAYS_KEEP,
    } for field in FEATURES]).sort_values(
        ["selected_by_l1", "selection_score_abs_l1_coefficient_sum"],
        ascending=[False, False]).to_csv(RESULTS / "app_ready_selected_fields.csv", index=False)
    pd.DataFrame([{
        "field": field,
        "required_by_selected_model": field in deployed_fields,
        "model": winner_name,
        "input_set": winner_inputs,
    } for field in FEATURES]).to_csv(RESULTS / "app_ready_model_inputs.csv", index=False)
    pd.DataFrame({
        ID: test[ID].to_numpy(),
        "actual_higher_beck_score_11plus": y_test.to_numpy(),
        "predicted_higher_beck_score_11plus": (probability >= THRESHOLD).astype(int),
        "predicted_probability": probability,
    }).to_csv(RESULTS / "app_ready_test_predictions.csv", index=False)
    pd.DataFrame({
        ID: test[ID].to_numpy(),
        "actual_higher_beck_score_11plus": y_test.to_numpy(),
        "predicted_higher_beck_score_11plus": (compact_probability >= THRESHOLD).astype(int),
        "predicted_probability": compact_probability,
    }).to_csv(RESULTS / "app_ready_compact_test_predictions.csv", index=False)
    pd.DataFrame([{
        "field": field, "required_by_selected_model": field in compact_fields,
        "model": compact_name, "input_set": compact_inputs,
    } for field in FEATURES]).to_csv(RESULTS / "app_ready_compact_model_inputs.csv", index=False)
    joblib.dump(best, MODELS / "best_app_ready_depression_model.joblib")
    joblib.dump(compact_best, MODELS / "best_compact_app_ready_depression_model.joblib")

    shown = summary[["model", "input_set", "cv_pr_auc_mean", "cv_pr_auc_sd", "selected_for_test", "selected_compact_for_test", "test_pr_auc", "test_precision", "test_recall"]].sort_values("cv_pr_auc_mean", ascending=False)
    print(shown.round(3).to_string(index=False))
    print(f"Selected overall by training CV PR-AUC: {winner_name} ({winner_inputs})")
    print(f"Selected compact model by training CV PR-AUC: {compact_name} ({compact_inputs})")
    print(f"Full model requires {len(deployed_fields)} fields: {', '.join(deployed_fields)}")
    print(f"Compact model requires {len(compact_fields)} fields: {', '.join(compact_fields)}")
    print(f"Full-model held-out metrics at threshold {THRESHOLD:.2f}: {test_metrics(y_test, probability)}")
    print(f"Compact-model held-out metrics at threshold {THRESHOLD:.2f}: {compact_metrics}")
    print(f"Saved results under {RESULTS}")


if __name__ == "__main__":
    main()

