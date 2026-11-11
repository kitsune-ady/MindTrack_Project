# MindTrack Project

## Study focus

Following the lecturer's feedback, the current project focuses on **depression as the single prediction target**. Phone-use habits and the recalculated phone-dependence total are candidate predictors. A separate phone-dependence prediction task is out of scope for this version.

## Source data

The original questionnaire workbooks and supporting documents are stored in `Digital Sedentary Behavior, Mobile Device Dependen/`. The source files are unchanged.

## Project structure

```text
MindTrack_Project/
├── Digital Sedentary Behavior, Mobile Device Dependen/  # Original workbooks and questionnaires
├── analysis/
│   ├── eda/
│       ├── README.md
│       ├── generate_eda.py
│       ├── requirements-eda.txt
│       ├── preliminary_eda_findings.md
│       ├── figures/
│       │   └── presentation/                            # Curated set of 10 charts
│       └── tables/                                      # Six CSV summaries and checks
│   └── cleaning/
│       ├── README.md
│       └── prepare_depression_dataset.py
│   └── pca/
│       ├── README.md
│       ├── run_pca_eda.py
│       ├── figures/                                      # Scree and PC1/PC2 charts
│       └── tables/                                       # Variance and loading tables
│   └── modeling/
│       ├── README.md
│       ├── requirements-modeling.txt
│       └── run_depression_models.py
├── data/
│   └── processed/                                       # Derived analysis CSV and preparation log
│   └── splits/                                          # Saved stratified 80% train and 20% test CSVs
├── results/                                             # Created when the modeling workflow is run
├── models/                                              # Fitted model saved by the workflow
├── notebooks/
│   └── Pipeline.ipynb                                   # Lecturer-facing end-to-end walkthrough
└── README.md
```

## Current status

The depression-focused EDA is complete under `analysis/eda/`. A reproducible preparation script and derived analysis dataset are under `analysis/cleaning/` and `data/processed/`. Exploratory PCA outputs are under `analysis/pca/`; predictive PCA is fitted within training folds. The depression-only modeling workflow is under `analysis/modeling/`. `notebooks/Pipeline.ipynb` walks a reviewer through the complete workflow and outputs. The raw data has not been modified. The target is the project-defined Beck score group >=11, not a clinical diagnosis. See `presentation_target_wording.md` for consistent presentation language.

## Next steps

1. Confirm that the Beck questionnaire form matches the scoring guide; document the decision to use the project-defined ≥11 score group.
2. Rerun python analysis/modeling/run_app_ready_models.py to save both the full Gradient Boosting pipeline and the compact 11-field Random Forest pipeline plus their input lists.
3. For the lecturer demo, use the compact input list to build a multi-step Android form, calculate TMD total from its 22 answers, and connect it to the Python prediction service. Label the output as an estimated Beck 11+ score group, not a diagnosis.
