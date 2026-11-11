# Depression score-group model comparison

The target is the project-defined Beck >=11 score group (`Higher_Beck_Score_11plus`). It combines the 11–16 mild mood-disturbance band with all higher bands; it is not a clinical diagnosis.
- Records: 1220; positive score-group records: 218 (17.9%).
- Stratified split: 80% training (976 records; 174 positives), 20% test (244 records; 44 positives); seed 42.
- Compared a most-common baseline with logistic regression, decision tree, random forest, and gradient boosting.
- Each classifier was fit without PCA and with PCA retaining 80% of the training-fold predictor variance.
- Repeated stratified 5-fold CV with 3 repeats was run on the training split. Encoding, scaling, and PCA are fit inside each fold.
- Models are selected by mean CV PR-AUC. Test metrics use a fixed probability threshold of 0.50; the test data was held out until final evaluation.
- The following permutation importance is measured on the held-out test data for the CV-selected model. It describes predictive usefulness in this dataset, not causation, and was not used to select features.
- Selected by CV PR-AUC: Gradient boosting (PCA: No).

## Top five permutation-importance inputs

| Feature | Mean PR-AUC drop when shuffled | SD |
|---|---:|---:|
| TMD_Total_Recomputed | 0.0253 | 0.0174 |
| Department | 0.0174 | 0.0159 |
| Age | 0.0143 | 0.0228 |
| Family_Expression | 0.0126 | 0.0126 |
| Living_Arrangement | 0.0102 | 0.0102 |

See `results/depression_model_comparison.csv` for cross-validation and test metrics, and `results/best_model_permutation_importance.csv` for all input fields.
The 0.50 threshold is a reporting choice, not a clinical rule. Interpret precision/recall alongside class imbalance and the project-defined 11+ score-group definition.
