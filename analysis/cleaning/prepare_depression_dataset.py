from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Digital Sedentary Behavior, Mobile Device Dependen"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)


def require_unique_codes(frame: pd.DataFrame, label: str) -> None:
    if frame["Code"].isna().any() or frame["Code"].duplicated().any():
        raise ValueError(f"{label}: student codes must be present and unique")


def main() -> None:
    socio = pd.read_excel(SOURCE / "2. Dataset_Sociodemo.xlsx", sheet_name="SocioDemo_data")
    tmd = pd.read_excel(SOURCE / "3. Dataset_MobileDependence.xlsx", sheet_name="TMD_data")
    beck = pd.read_excel(SOURCE / "5. Dataset_Depression.xlsx", sheet_name="Depression_data")

    for frame, label in ((socio, "sociodemographic"), (tmd, "TMD"), (beck, "Beck")):
        require_unique_codes(frame, label)
    if not socio["Code"].equals(tmd["Code"]) or not socio["Code"].equals(beck["Code"]):
        raise ValueError("Student codes differ in value or order across source workbooks")

    tmd_items = list(tmd.columns[8:30])
    beck_items = list(beck.columns[8:29])
    tmd_answers = tmd[tmd_items].apply(pd.to_numeric, errors="coerce")
    beck_answers = beck[beck_items].apply(pd.to_numeric, errors="coerce")
    beck_total = pd.to_numeric(beck["Sum"], errors="coerce")
    if tmd_answers.isna().any().any() or beck_answers.isna().any().any() or beck_total.isna().any():
        raise ValueError("Unexpected missing/non-numeric questionnaire answer or Beck total")

    # Recompute this score because the EDA found one inconsistent supplied total.
    tmd_total = tmd_answers.sum(axis=1)
    if not beck_answers.sum(axis=1).equals(beck_total):
        raise ValueError("Beck Sum does not match the 21 item answers; investigate scoring")

    socio_predictors = [
        "Age", "Semester", "Department", "Sex", "MS", "SES", "Living_Arrangement",
        "Family_Expression", "Family_Activities", "Mobile_Use_Rules",
        "Phone_Discrimination", "Phone_Related_Arguments", "Residence_Area",
        "Subscription_Plan", "Network _Access", "Areas_Use", "Time_First_Cellphone",
        "Type_MD", "Using_Text Messaging_Apps", "Using_Games_Apps",
        "Using_social media_Apps", "Using_Music_Apps", "Using_Videos_Apps",
        "Using_Ttime-management_Apps", "Using_Camara_Apps", "Using_Mail_Apps",
        "Average_Time_Use",
    ]
    missing = [c for c in socio_predictors if c not in socio.columns]
    if missing:
        raise ValueError(f"Missing expected predictor columns: {missing}")

    output = socio[["Code", *socio_predictors]].copy()
    for item in tmd_items:
        output[f"TMD_{item.strip().replace(' ', '_')}"] = tmd_answers[item].to_numpy()
    output["TMD_Total_Recomputed"] = tmd_total.to_numpy()
    output["Beck_Total"] = beck_total.to_numpy()
    output["Higher_Beck_Score_11plus"] = (beck_total >= 11).astype("int8").to_numpy()
    if output.isna().any().any():
        raise ValueError(f"Unexpected missing values in prepared data: {output.columns[output.isna().any()].tolist()}")

    output.to_csv(OUT / "depression_analysis_dataset.csv", index=False)
    mismatch = pd.to_numeric(tmd["sum"], errors="coerce").ne(tmd_total)
    positives = int(output["Higher_Beck_Score_11plus"].sum())
    summary = [
        "# Depression analysis dataset: preparation log", "",
        f"- Records retained: {len(output)}; source IDs aligned one-to-one.",
        f"- Candidate predictors: {len(socio_predictors) + len(tmd_items) + 1} (background, phone-use responses, 22 TMD items, and recomputed TMD total).",
        "- Beck total (`Beck_Total`) is the score outcome/reference, not an input feature.",
        f"- Project target `Higher_Beck_Score_11plus`: 1 for Beck total >= 11; positives {positives}, negatives {len(output) - positives}.",
        "- This is a project-defined questionnaire score group for research, not a clinical diagnosis.",
        f"- TMD total was recomputed from 22 answers; {int(mismatch.sum())} supplied total(s) differed and were not used.",
        "- Beck total matched the sum of its 21 answers for every record.",
        "- No missing values were found in the prepared columns; no imputation or row deletion was needed.",
        "- Excluded from predictors: Code (identifier), Beck item answers and result label (target leakage), supplied TMD sum/level (replaced by recomputed total), Program (overlaps with Department and has many categories), posture/ergonomics fields, and anxiety fields.",
        "- Source category codes are retained. Encoding, scaling, feature selection, and optional PCA must be fitted only within training folds after the split.",
        "- Both TMD items and total are retained for exploration. For modeling, compare an item-level feature set with a total-score feature set rather than using both together by default.",
        "", "## Output", "", "`data/processed/depression_analysis_dataset.csv`", "",
        "Original workbooks were not modified.",
    ]
    (OUT / "preparation_log.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"Prepared {len(output)} records; project-defined 11+ score group: {positives}; wrote {OUT}")


if __name__ == "__main__":
    main()
