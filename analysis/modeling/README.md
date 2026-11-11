# Depression score-group modeling

This workflow predicts the project-defined Beck score group of 11 or higher from the agreed background and phone-use inputs plus the recalculated phone-dependence total. The target is a research score grouping, not a clinical diagnosis.

## Run from the project root

```bash
python -m pip install -r analysis/modeling/requirements-modeling.txt
python analysis/modeling/run_depression_models.py
```

The script makes a stratified 80/20 train/test split. It compares a most-common baseline with logistic regression, decision tree, random forest, and gradient boosting. Each classifier is compared without PCA and with PCA retaining 80% of variance. Repeated stratified 5-fold cross-validation with 3 repeats is performed on the training split. The test set is held out for final evaluation.

The exact split is saved to `data/splits/depression_train_80pct.csv` and `data/splits/depression_test_20pct.csv`. Both include `Code` for row traceability, but the modeling pipeline excludes it from predictors. The target is `Higher_Beck_Score_11plus`; Beck total and Beck item answers are omitted to avoid target leakage.

To create or refresh only the split CSVs without rerunning cross-validation, use:

```bash
python analysis/modeling/run_depression_models.py --split-only
```

Imputing, encoding, scaling, and PCA are inside the pipelines and fit only on training folds. Student Code, Beck item responses, Beck total, and the supplied TMD item answers are not predictors. The model uses the recalculated phone-dependence total.

Model selection is based on mean CV PR-AUC. Test metrics use a fixed probability threshold of 0.50. The script also reports permutation importance by original input field for the model selected by CV; this indicates predictive usefulness in this dataset, not causation.

## Outputs

- `results/depression_model_comparison.csv` — CV and held-out metrics for each model/PCA variant.
- `results/depression_repeated_cv_folds.csv` — per-fold CV scores.
- `results/best_model_test_predictions.csv` — held-out predictions for the CV-selected model.
- `results/best_model_permutation_importance.csv` — input fields ranked by PR-AUC decrease when shuffled.
- `results/modeling_summary.md` — plain-language method summary and top importance values.
- `models/best_depression_model.joblib` — selected fitted pipeline, trained on the 80% split.

The project groups Beck scores into <11 and >=11. This combines the codebook 11–16 mild mood-disturbance band with all higher bands. Confirm with the lecturer that the Beck form and scoring guide match before presenting this as a depression classification.

## App-ready model comparison

The input proposal is documented in [app_input_schema.md](app_input_schema.md). Run the app-ready comparison from the project root:

```bash
python analysis/modeling/run_app_ready_models.py
```

This compares the baseline and four classifiers using (a) all 27 app-compatible candidate fields and (b) a reduced field set. The reduced set uses grouped L1 logistic-regression coefficient scores fitted inside each training fold; TMD_Total_Recomputed is always kept. Average_Time_Use is excluded because its 1–3 hour category has one response. PCA is omitted from this deployment-focused comparison.

The script reuses the saved 80/20 split. Repeated training CV PR-AUC selects the overall model and the best L1-reduced model separately; the saved holdout reports both candidates but is not used to select either. It has already been reviewed during the broader-model work, so treat both test estimates as preliminary. In the current run, full-input Gradient Boosting led CV (PR-AUC 0.287); the compact Random Forest used 11 fields (PR-AUC 0.262). Outputs include results/app_ready_model_comparison.csv, results/app_ready_model_inputs.csv, results/app_ready_compact_model_inputs.csv, results/app_ready_selected_fields.csv, both test-prediction files, and models/best_app_ready_depression_model.joblib plus models/best_compact_app_ready_depression_model.joblib. The compact form needs the fields in app_ready_compact_model_inputs.csv and must calculate TMD total from the 22 TMD answers.
