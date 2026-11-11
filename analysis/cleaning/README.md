# Depression dataset preparation

This step follows the EDA and creates an analysis table for the single-target depression study. The binary outcome is named `Higher_Beck_Score_11plus` to make clear that it is a project-defined Beck score group (11 or higher), not a clinical diagnosis. It combines score bands 11–16 and all higher bands.

## Run from the project root

```bash
python -m pip install -r analysis/eda/requirements-eda.txt
python analysis/cleaning/prepare_depression_dataset.py
```

The script checks ID alignment and scoring, recomputes the phone-dependence total from its 22 responses, and writes a derived CSV and preparation log to `data/processed/`. It does not change the source workbooks.

Source category codes are preserved. Encoding, scaling, PCA, feature selection, and other learned transformations belong inside a training pipeline after the train/test split, so held-out data cannot influence fitting.

The table retains both TMD item answers and their recomputed total for exploration. For modeling, compare an item-level input set with a total-score input set rather than using both representations together by default.
