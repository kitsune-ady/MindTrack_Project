# PCA exploratory analysis

- Records included: 1220.
- Encoded predictor columns before removal of constants: 28 source fields.
- PCA dimensions after one-hot encoding and removal of constant columns: 57.
- PC1 explains 14.5%; PC2 explains 6.3%; first two together explain 20.8% of predictor variation.
- Components needed to reach 80% cumulative variance: 27.
- Predictors included age, semester, department, demographic and phone-use responses, app-selection flags, and the recomputed phone-dependence total. The 22 TMD items were left out because the selected analysis uses the total score.
- Beck total, the 11+ score-group outcome, and student Code were excluded from PCA. The 11+ score-group flag is used only to color the PC1/PC2 visualization.
- Nominal categories were one-hot encoded. Ordered responses were retained as ordered numeric codes, app-selection flags were converted from 1/2 to 0/1, and all resulting columns were standardized before PCA.
- This is full-dataset exploratory PCA for descriptive visualization and loadings. Do not use these fitted components as model inputs: for prediction, split first and fit encoding, scaling, and PCA inside each training fold.
- PCA captures variation among predictors; it does not show cause and effect or prove that the groups can be predicted accurately.
