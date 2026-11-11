# Depression analysis dataset: preparation log

- Records retained: 1220; source IDs aligned one-to-one.
- Candidate predictors: 50 (background, phone-use responses, 22 TMD items, and recomputed TMD total).
- Beck total (`Beck_Total`) is the score outcome/reference, not an input feature.
- Project target `Higher_Beck_Score_11plus`: 1 for Beck total >= 11; positives 218, negatives 1002.
- This is a project-defined questionnaire score group for research, not a clinical diagnosis.
- TMD total was recomputed from 22 answers; 1 supplied total(s) differed and were not used.
- Beck total matched the sum of its 21 answers for every record.
- No missing values were found in the prepared columns; no imputation or row deletion was needed.
- Excluded from predictors: Code (identifier), Beck item answers and result label (target leakage), supplied TMD sum/level (replaced by recomputed total), Program (overlaps with Department and has many categories), posture/ergonomics fields, and anxiety fields.
- Source category codes are retained. Encoding, scaling, feature selection, and optional PCA must be fitted only within training folds after the split.
- Both TMD items and total are retained for exploration. For modeling, compare an item-level feature set with a total-score feature set rather than using both together by default.

## Output

`data/processed/depression_analysis_dataset.csv`

Original workbooks were not modified.
