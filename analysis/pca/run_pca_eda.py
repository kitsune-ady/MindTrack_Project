from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data" / "processed" / "depression_analysis_dataset.csv"
OUT = Path(__file__).resolve().parent
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
TABLES.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

NOMINAL = [
    "Department", "Sex", "MS", "SES", "Living_Arrangement", "Residence_Area",
    "Subscription_Plan", "Network _Access", "Areas_Use", "Type_MD",
]
ORDINAL = [
    "Semester", "Family_Expression", "Family_Activities", "Mobile_Use_Rules",
    "Phone_Discrimination", "Phone_Related_Arguments", "Time_First_Cellphone",
    "Average_Time_Use",
]
CONTINUOUS = ["Age", "TMD_Total_Recomputed"]
APP_FLAGS = [
    "Using_Text Messaging_Apps", "Using_Games_Apps", "Using_social media_Apps",
    "Using_Music_Apps", "Using_Videos_Apps", "Using_Ttime-management_Apps",
    "Using_Camara_Apps", "Using_Mail_Apps",
]


def get_font(size: int, bold: bool = False):
    for path in ([r"C:\Windows\Fonts\arialbd.ttf"] if bold else []) + [r"C:\Windows\Fonts\arial.ttf"]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def centered(draw, x, y, text, font, fill="#243746"):
    box = draw.textbbox((0, 0), str(text), font=font)
    draw.text((x - (box[2] - box[0]) / 2, y - (box[3] - box[1]) / 2), str(text), font=font, fill=fill)


def save_variance_chart(variance: np.ndarray, cumulative: np.ndarray) -> None:
    width, height = 1450, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    navy, blue, green, grid, ink = "#17324D", "#4C78A8", "#59A14F", "#D9E1EA", "#263746"
    draw.text((65, 35), "PCA explained variance", font=get_font(32, True), fill=navy)
    draw.text((67, 83), "Standardized predictors; depression outcome excluded from PCA", font=get_font(18), fill="#5E6D7B")
    left, top, right, bottom = 110, 150, 1355, 720
    max_pct = max(0.2, min(1.0, float(cumulative[min(len(cumulative), 20) - 1]) * 1.08))
    max_pct = max(0.5, np.ceil(max_pct * 10) / 10)
    for tick in np.arange(0, max_pct + 0.001, 0.1):
        y = bottom - (bottom - top) * tick / max_pct
        draw.line((left, y, right, y), fill=grid, width=1)
        draw.text((55, y - 9), f"{tick:.0%}", font=get_font(15), fill=ink)
    n = min(len(variance), 20)
    slot = (right - left) / n
    for i in range(n):
        x = left + i * slot + slot * 0.2
        bar_right = left + (i + 1) * slot - slot * 0.2
        y = bottom - (bottom - top) * float(variance[i]) / max_pct
        draw.rectangle((x, y, bar_right, bottom), fill=blue)
        centered(draw, (x + bar_right) / 2, bottom + 20, f"{i + 1}", get_font(14), ink)
    points = []
    for i in range(n):
        x = left + (i + 0.5) * slot
        y = bottom - (bottom - top) * float(cumulative[i]) / max_pct
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=green, width=4)
    for x, y in points:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=green)
    draw.line((left, top, left, bottom, right, bottom), fill=ink, width=2)
    draw.text((left, 755), "Principal component", font=get_font(17), fill=ink)
    draw.text((left, 790), "Blue bars: individual variance   Green line: cumulative variance", font=get_font(18), fill=navy)
    draw.text((left, 830), f"Components for 80%: {int(np.searchsorted(cumulative, 0.8) + 1)}", font=get_font(18, True), fill=navy)
    image.save(FIGURES / "01_pca_scree_cumulative_variance.png")


def save_score_plot(scores: np.ndarray, target: pd.Series, variance: np.ndarray) -> None:
    width, height = 1450, 950
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    navy, grid, ink = "#17324D", "#D9E1EA", "#263746"
    draw.text((65, 35), "Students projected onto PC1 and PC2", font=get_font(31, True), fill=navy)
    draw.text((67, 82), "PCA uses predictors only; color shows the project-defined Beck score group", font=get_font(18), fill="#5E6D7B")
    left, top, right, bottom = 140, 160, 1350, 750
    x, y = scores[:, 0], scores[:, 1]
    xlim = (float(x.min()), float(x.max()))
    ylim = (float(y.min()), float(y.max()))
    xpad = (xlim[1] - xlim[0]) * 0.06 or 1
    ypad = (ylim[1] - ylim[0]) * 0.06 or 1
    xlim = (xlim[0] - xpad, xlim[1] + xpad)
    ylim = (ylim[0] - ypad, ylim[1] + ypad)
    for i in range(5):
        gx = left + (right - left) * i / 4
        gy = top + (bottom - top) * i / 4
        draw.line((gx, top, gx, bottom), fill=grid)
        draw.line((left, gy, right, gy), fill=grid)
        xv = xlim[0] + (xlim[1] - xlim[0]) * i / 4
        yv = ylim[1] - (ylim[1] - ylim[0]) * i / 4
        centered(draw, gx, bottom + 22, f"{xv:.1f}", get_font(14), ink)
        draw.text((65, gy - 8), f"{yv:.1f}", font=get_font(14), fill=ink)
    colors = {0: "#4C78A8", 1: "#D95F59"}
    for px, py, label in zip(x, y, target.astype(int)):
        sx = left + (px - xlim[0]) / (xlim[1] - xlim[0]) * (right - left)
        sy = bottom - (py - ylim[0]) / (ylim[1] - ylim[0]) * (bottom - top)
        color = colors[int(label)]
        draw.ellipse((sx - 3, sy - 3, sx + 3, sy + 3), fill=color)
    draw.line((left, top, left, bottom, right, bottom), fill=ink, width=2)
    draw.text((left, 800), f"PC1 ({variance[0]:.1%} variance)", font=get_font(17, True), fill=navy)
    draw.text((left, 830), f"PC2 ({variance[1]:.1%} variance)", font=get_font(17, True), fill=navy)
    draw.ellipse((left + 320, 799, left + 336, 815), fill=colors[0])
    draw.text((left + 345, 798), "Below 11", font=get_font(16), fill=ink)
    draw.ellipse((left + 470, 799, left + 486, 815), fill=colors[1])
    draw.text((left + 495, 798), "11+ score group", font=get_font(16), fill=ink)
    draw.text((left, 875), "Visualization only: overlap/separation is not a test of predictive performance.", font=get_font(16), fill="#5E6D7B")
    image.save(FIGURES / "02_pca_pc1_pc2_by_beck_group.png")


def main() -> None:
    data = pd.read_csv(SOURCE)
    required = NOMINAL + ORDINAL + CONTINUOUS + APP_FLAGS + ["Code", "Beck_Total", "Higher_Beck_Score_11plus"]
    missing = [col for col in required if col not in data.columns]
    if missing:
        raise ValueError(f"Prepared dataset is missing expected columns: {missing}")

    # Use the previously selected total-score representation, not its 22 component items.
    predictors = data[NOMINAL + ORDINAL + CONTINUOUS + APP_FLAGS].copy()
    if predictors.isna().any().any():
        raise ValueError("PCA inputs contain missing data; resolve before PCA")

    # Binary flags are stored as 1=No, 2=Yes in the workbook; represent them as 0/1.
    predictors[APP_FLAGS] = predictors[APP_FLAGS].replace({1: 0, 2: 1})
    encoded = pd.get_dummies(predictors, columns=NOMINAL, prefix=NOMINAL, dtype=float)
    encoded = encoded.apply(pd.to_numeric, errors="raise").astype(float)
    means = encoded.mean(axis=0)
    scales = encoded.std(axis=0, ddof=0)
    keep = scales > 1e-12
    encoded = encoded.loc[:, keep]
    means = means.loc[keep]
    scales = scales.loc[keep]
    standardized = ((encoded - means) / scales).to_numpy(dtype=float)

    # SVD is used directly so the PCA remains reproducible with NumPy alone.
    _, singular_values, right_vectors = np.linalg.svd(standardized, full_matrices=False)
    eigenvalues = singular_values**2 / (len(standardized) - 1)
    variance_ratio = eigenvalues / eigenvalues.sum()
    cumulative = np.cumsum(variance_ratio)
    scores = standardized @ right_vectors.T
    n_components = min(10, right_vectors.shape[0])

    pd.DataFrame({
        "component": [f"PC{i + 1}" for i in range(len(variance_ratio))],
        "explained_variance_ratio": variance_ratio,
        "cumulative_variance_ratio": cumulative,
        "eigenvalue": eigenvalues,
    }).to_csv(TABLES / "pca_explained_variance.csv", index=False)

    # Correlations between standardized input columns and component scores.
    loadings = right_vectors.T * np.sqrt(eigenvalues[:, None])
    loading_table = pd.DataFrame(loadings[:n_components].T, index=encoded.columns,
                                 columns=[f"PC{i + 1}" for i in range(n_components)])
    loading_table.index.name = "encoded_predictor"
    loading_table.reset_index().to_csv(TABLES / "pca_loadings_top10.csv", index=False)

    score_table = pd.DataFrame({
        "Code": data["Code"],
        "PC1": scores[:, 0],
        "PC2": scores[:, 1],
        "Higher_Beck_Score_11plus_for_plot_color_only": data["Higher_Beck_Score_11plus"],
    })
    score_table.to_csv(TABLES / "pca_student_scores_pc1_pc2.csv", index=False)
    save_variance_chart(variance_ratio, cumulative)
    save_score_plot(scores, data["Higher_Beck_Score_11plus"], variance_ratio)

    report = [
        "# PCA exploratory analysis", "",
        f"- Records included: {len(data)}.",
        f"- Encoded predictor columns before removal of constants: {len(NOMINAL) + len(ORDINAL) + len(CONTINUOUS) + len(APP_FLAGS)} source fields.",
        f"- PCA dimensions after one-hot encoding and removal of constant columns: {encoded.shape[1]}.",
        f"- PC1 explains {variance_ratio[0]:.1%}; PC2 explains {variance_ratio[1]:.1%}; first two together explain {cumulative[1]:.1%} of predictor variation.",
        f"- Components needed to reach 80% cumulative variance: {int(np.searchsorted(cumulative, 0.8) + 1)}.",
        "- Predictors included age, semester, department, demographic and phone-use responses, app-selection flags, and the recomputed phone-dependence total. The 22 TMD items were left out because the selected analysis uses the total score.",
        "- Beck total, the 11+ score-group outcome, and student Code were excluded from PCA. The 11+ score-group flag is used only to color the PC1/PC2 visualization.",
        "- Nominal categories were one-hot encoded. Ordered responses were retained as ordered numeric codes, app-selection flags were converted from 1/2 to 0/1, and all resulting columns were standardized before PCA.",
        "- This is full-dataset exploratory PCA for descriptive visualization and loadings. Do not use these fitted components as model inputs: for prediction, split first and fit encoding, scaling, and PCA inside each training fold.",
        "- PCA captures variation among predictors; it does not show cause and effect or prove that the groups can be predicted accurately.",
    ]
    (OUT / "pca_findings.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"PCA complete: {encoded.shape[1]} dimensions; PC1+PC2 explain {cumulative[1]:.1%}; 80% reached at {int(np.searchsorted(cumulative, 0.8) + 1)} components")


if __name__ == "__main__":
    main()
