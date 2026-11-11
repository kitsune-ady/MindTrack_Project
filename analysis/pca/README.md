# PCA exploratory analysis

This PCA explores patterns among the cleaned predictor variables before modeling. It uses the recalculated phone-dependence total selected for the project and excludes the 22 individual TMD items, the Beck score and target, and student Code.

## Run from the project root

```bash
python -m pip install -r analysis/eda/requirements-eda.txt
python analysis/pca/run_pca_eda.py
```

The script writes its charts, tables, and short interpretation under `analysis/pca/`. It uses NumPy SVD for PCA and Pillow for chart images.

## Outputs

- `figures/01_pca_scree_cumulative_variance.png` — variance explained by each component and cumulatively.
- `figures/02_pca_pc1_pc2_by_beck_group.png` — student projection onto PC1 and PC2, colored by the project-defined 11+ score group. The outcome is used only for coloring, not to calculate PCA.
- `tables/pca_explained_variance.csv` — variance and cumulative variance for every component.
- `tables/pca_loadings_top10.csv` — input loadings for the first 10 components.
- `tables/pca_student_scores_pc1_pc2.csv` — two component scores and target color label for each student; Code is included only for row traceability and must not be a model input.

This full-dataset PCA is for exploration and presentation only. Its fitted components must not be used for predictive evaluation. If PCA is included in a model, split the data first and fit encoding, scaling, and PCA within each training fold.
