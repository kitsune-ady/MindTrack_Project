import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.class_weight import compute_sample_weight


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "depression_analysis_dataset.csv"
RESULTS = ROOT / "results"
MODELS = ROOT / "models"
SPLITS = ROOT / "data" / "splits"
RESULTS.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)
SPLITS.mkdir(parents=True, exist_ok=True)
SEED = 42
THRESHOLD = 0.50
TARGET = "Higher_Beck_Score_11plus"
ID = "Code"

NOMINAL = [
    "Department", "Sex", "MS", "SES", "Living_Arrangement", "Residence_Area",
    "Subscription_Plan", "Network _Access", "Areas_Use", "Type_MD",
]
ORDERED_AND_NUMERIC = [
    "Age", "Semester", "Family_Expression", "Family_Activities", "Mobile_Use_Rules",
    "Phone_Discrimination", "Phone_Related_Arguments", "Time_First_Cellphone",
    "Average_Time_Use", "TMD_Total_Recomputed",
]
APP_FLAGS = [
    "Using_Text Messaging_Apps", "Using_Games_Apps", "Using_social media_Apps",
    "Using_Music_Apps", "Using_Videos_Apps", "Using_Ttime-management_Apps",
    "Using_Camara_Apps", "Using_Mail_Apps",
]
FEATURES = NOMINAL + ORDERED_AND_NUMERIC + APP_FLAGS


def make_preprocessor() -> ColumnTransformer:
    try:
        one_hot = OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:  # Compatibility with older scikit-learn versions.
        one_hot = OneHotEncoder(handle_unknown="ignore", sparse=False)
    return ColumnTransformer(
        transformers=[
            ("numeric", Pipeline([
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
            ]), ORDERED_AND_NUMERIC + APP_FLAGS),
            ("categorical", Pipeline([
                ("impute", SimpleImputer(strategy="most_frequent")),
                ("onehot", one_hot),
            ]), NOMINAL),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def make_pipeline(estimator, use_pca: bool) -> Pipeline:
    steps = [("preprocess", make_preprocessor()), ("scale_encoded", StandardScaler())]
    if use_pca:
        # PCA is fitted only on training data inside each CV fold.
        steps.append(("pca", PCA(n_components=0.80, svd_solver="full")))
    steps.append(("model", estimator))
    return Pipeline(steps)


def metrics(y_true, probabilities):
    predicted = (probabilities >= THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    return {
        "test_accuracy": accuracy_score(y_true, predicted),
        "test_precision": precision_score(y_true, predicted, zero_division=0),
        "test_recall": recall_score(y_true, predicted, zero_division=0),
        "test_f1": f1_score(y_true, predicted, zero_division=0),
        "test_balanced_accuracy": balanced_accuracy_score(y_true, predicted),
        "test_roc_auc": roc_auc_score(y_true, probabilities),
        "test_pr_auc": average_precision_score(y_true, probabilities),
        "test_tn": int(tn), "test_fp": int(fp), "test_fn": int(fn), "test_tp": int(tp),
    }


def model_specs():
    return {
        "Baseline (most common)": [("No", DummyClassifier(strategy="most_frequent"))],
        "Logistic regression": [
            ("No", LogisticRegression(max_iter=3000, solver="liblinear", random_state=SEED)),
            ("Yes", LogisticRegression(max_iter=3000, solver="liblinear", random_state=SEED)),
        ],
        "Decision tree": [
            ("No", DecisionTreeClassifier(max_depth=5, min_samples_leaf=10, random_state=SEED)),
            ("Yes", DecisionTreeClassifier(max_depth=5, min_samples_leaf=10, random_state=SEED)),
        ],
        "Random forest": [
            ("No", RandomForestClassifier(n_estimators=400, max_features="sqrt", min_samples_leaf=4, n_jobs=-1, random_state=SEED)),
            ("Yes", RandomForestClassifier(n_estimators=400, max_features="sqrt", min_samples_leaf=4, n_jobs=-1, random_state=SEED)),
        ],
        "Gradient boosting": [
            ("No", GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=2, min_samples_leaf=10, random_state=SEED)),
            ("Yes", GradientBoostingClassifier(n_estimators=150, learning_rate=0.05, max_depth=2, min_samples_leaf=10, random_state=SEED)),
        ],
    }


def main(split_only: bool = False) -> None:
    data = pd.read_csv(DATA_PATH)
    required = FEATURES + [ID, "Beck_Total", TARGET]
    missing = [column for column in required if column not in data]
    if missing:
        raise ValueError(f"Prepared dataset is missing expected columns: {missing}")
    if data[FEATURES + [TARGET]].isna().any().any():
        raise ValueError("Model inputs or target contain missing values")

    X = data[FEATURES].copy()
    # Source dictionary records app flags as 1=No and 2=Yes.
    for column in APP_FLAGS:
        values = set(pd.to_numeric(X[column], errors="raise").unique())
        if not values.issubset({1, 2}):
            raise ValueError(f"Unexpected codes in app flag {column}: {values}")
        X[column] = X[column].map({1: 0, 2: 1})
    y = data[TARGET].astype(int)
    if set(y.unique()) != {0, 1}:
        raise ValueError("The target must contain both score groups")

    X_train, X_test, y_train, y_test, id_train, id_test = train_test_split(
        X, y, data[ID], test_size=0.20, random_state=SEED, stratify=y
    )
    # Save the exact split used below. Code is retained only for row traceability;
    # it is excluded from FEATURES and is never passed to a model.
    train_export = X_train.copy()
    train_export.insert(0, ID, id_train.to_numpy())
    train_export[TARGET] = y_train.to_numpy()
    train_export.to_csv(SPLITS / "depression_train_80pct.csv", index=False)
    test_export = X_test.copy()
    test_export.insert(0, ID, id_test.to_numpy())
    test_export[TARGET] = y_test.to_numpy()
    test_export.to_csv(SPLITS / "depression_test_20pct.csv", index=False)
    split_note = [
        "# Saved modeling split", "",
        f"- Training file: `data/splits/depression_train_80pct.csv` ({len(train_export)} records; {int(y_train.sum())} 11+ records).",
        f"- Test file: `data/splits/depression_test_20pct.csv` ({len(test_export)} records; {int(y_test.sum())} 11+ records).",
        f"- Split: stratified 80/20, random seed {SEED}.",
        f"- Target: `{TARGET}`. `Code` is included only to trace records and must not be used as a predictor.",
        "- Beck_Total, Beck answer items, and supplied TMD item answers are not included. Model inputs include the recomputed TMD total.",
        "- These same files correspond to the training and held-out test portions used by the modeling script.",
    ]
    (SPLITS / "README.md").write_text("\n".join(split_note) + "\n", encoding="utf-8")
    if split_only:
        print(f"Saved split only: train={len(train_export)} records, test={len(test_export)} records in {SPLITS}")
        return

    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)
    cv_indices = list(cv.split(X_train, y_train))
    fold_rows, final_rows, fitted_models = [], [], {}

    for model_name, variants in model_specs().items():
        for pca_label, estimator in variants:
            pipeline = estimator if model_name == "Baseline (most common)" else make_pipeline(estimator, pca_label == "Yes")
            for fold_number, (train_index, valid_index) in enumerate(cv_indices, start=1):
                X_fit, X_valid = X_train.iloc[train_index], X_train.iloc[valid_index]
                y_fit, y_valid = y_train.iloc[train_index], y_train.iloc[valid_index]
                fitted = clone(pipeline)
                if model_name == "Baseline (most common)":
                    fitted.fit(X_fit, y_fit)
                else:
                    fitted.fit(X_fit, y_fit, model__sample_weight=compute_sample_weight("balanced", y_fit))
                probability = fitted.predict_proba(X_valid)[:, 1]
                fold_rows.append({
                    "model": model_name, "pca": pca_label, "fold": fold_number,
                    "cv_roc_auc": roc_auc_score(y_valid, probability),
                    "cv_pr_auc": average_precision_score(y_valid, probability),
                    "cv_balanced_accuracy_at_0_50": balanced_accuracy_score(y_valid, (probability >= THRESHOLD).astype(int)),
                })

            final = clone(pipeline)
            if model_name == "Baseline (most common)":
                final.fit(X_train, y_train)
            else:
                final.fit(X_train, y_train, model__sample_weight=compute_sample_weight("balanced", y_train))
            probability = final.predict_proba(X_test)[:, 1]
            fitted_models[(model_name, pca_label)] = final
            final_rows.append({"model": model_name, "pca": pca_label, "threshold": THRESHOLD, **metrics(y_test, probability)})

    fold_frame = pd.DataFrame(fold_rows)
    cv_summary = fold_frame.groupby(["model", "pca"], as_index=False).agg(
        cv_roc_auc_mean=("cv_roc_auc", "mean"), cv_roc_auc_sd=("cv_roc_auc", "std"),
        cv_pr_auc_mean=("cv_pr_auc", "mean"), cv_pr_auc_sd=("cv_pr_auc", "std"),
        cv_balanced_accuracy_mean=("cv_balanced_accuracy_at_0_50", "mean"),
        cv_balanced_accuracy_sd=("cv_balanced_accuracy_at_0_50", "std"),
    )
    results = cv_summary.merge(pd.DataFrame(final_rows), on=["model", "pca"], how="outer")
    results["selection_basis"] = "Repeated-CV mean PR-AUC; test metrics are held-out evaluation"
    results.to_csv(RESULTS / "depression_model_comparison.csv", index=False)
    fold_frame.to_csv(RESULTS / "depression_repeated_cv_folds.csv", index=False)

    candidates = results[results.model != "Baseline (most common)"].dropna(subset=["cv_pr_auc_mean"])
    best_row = candidates.sort_values("cv_pr_auc_mean", ascending=False).iloc[0]
    best_key = (best_row.model, best_row.pca)
    best_model = fitted_models[best_key]
    best_probability = best_model.predict_proba(X_test)[:, 1]
    best_prediction = (best_probability >= THRESHOLD).astype(int)
    pd.DataFrame({
        "Code": id_test.to_numpy(),
        "actual_higher_beck_score_11plus": y_test.to_numpy(),
        "predicted_higher_beck_score_11plus": best_prediction,
        "predicted_probability": best_probability,
    }).to_csv(RESULTS / "best_model_test_predictions.csv", index=False)

    importance = permutation_importance(
        best_model, X_test, y_test, scoring="average_precision", n_repeats=20,
        random_state=SEED, n_jobs=-1,
    )
    importance_frame = pd.DataFrame({
        "feature": FEATURES,
        "permutation_importance_mean_pr_auc_drop": importance.importances_mean,
        "permutation_importance_sd": importance.importances_std,
    }).sort_values("permutation_importance_mean_pr_auc_drop", ascending=False)
    importance_frame.to_csv(RESULTS / "best_model_permutation_importance.csv", index=False)
    joblib.dump(best_model, MODELS / "best_depression_model.joblib")

    positive = int(y.sum())
    top = importance_frame.head(5)
    summary = [
        "# Depression score-group model comparison", "",
        "The target is the project-defined Beck >=11 score group (`Higher_Beck_Score_11plus`). It combines the 11–16 mild mood-disturbance band with all higher bands; it is not a clinical diagnosis.",
        f"- Records: {len(data)}; positive score-group records: {positive} ({positive / len(data):.1%}).",
        f"- Stratified split: 80% training ({len(X_train)} records; {int(y_train.sum())} positives), 20% test ({len(X_test)} records; {int(y_test.sum())} positives); seed {SEED}.",
        "- Compared a most-common baseline with logistic regression, decision tree, random forest, and gradient boosting.",
        "- Each classifier was fit without PCA and with PCA retaining 80% of the training-fold predictor variance.",
        "- Repeated stratified 5-fold CV with 3 repeats was run on the training split. Encoding, scaling, and PCA are fit inside each fold.",
        "- Models are selected by mean CV PR-AUC. Test metrics use a fixed probability threshold of 0.50; the test data was held out until final evaluation.",
        "- The following permutation importance is measured on the held-out test data for the CV-selected model. It describes predictive usefulness in this dataset, not causation, and was not used to select features.",
        f"- Selected by CV PR-AUC: {best_key[0]} (PCA: {best_key[1]}).", "",
        "## Top five permutation-importance inputs", "",
        "| Feature | Mean PR-AUC drop when shuffled | SD |", "|---|---:|---:|",
    ]
    for row in top.itertuples(index=False):
        summary.append(f"| {row.feature} | {row.permutation_importance_mean_pr_auc_drop:.4f} | {row.permutation_importance_sd:.4f} |")
    summary += [
        "", "See `results/depression_model_comparison.csv` for cross-validation and test metrics, and `results/best_model_permutation_importance.csv` for all input fields.",
        "The 0.50 threshold is a reporting choice, not a clinical rule. Interpret precision/recall alongside class imbalance and the project-defined 11+ score-group definition.",
    ]
    (RESULTS / "modeling_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"Finished: train={len(X_train)}, test={len(X_test)}, selected={best_key[0]} (PCA={best_key[1]})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split the dataset and compare depression score-group models.")
    parser.add_argument("--split-only", action="store_true", help="Save the stratified train/test CSVs without refitting models.")
    main(split_only=parser.parse_args().split_only)
