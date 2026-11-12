# Depression model: proposed app input contract

## Prediction task

There is one target: `Higher_Beck_Score_11plus`. The dataset dictionary groups BDI-2 scores 0-10 as normal and 11-16 as mild mood disturbance, followed by higher bands. For this project, 11+ is a dataset-defined higher-score group, not a diagnosis. The questionnaire file and data dictionary use potentially inconsistent Beck-version wording, so the team should verify the version and score rule with the lecturer before freezing the outcome.

Phone dependence is not a target. The recalculated TMD total remains an input to predict the depression group. The TMD source questionnaire has 22 items, each scored from 0 to 4, giving a total from 0 to 88. Items 1-10 use a frequency scale (Never to Very often); items 11-22 use an agreement scale (Strongly disagree to Strongly agree). Both scales must preserve the same numeric coding as the dataset. The app should calculate the total from the item responses; the user should not enter or calculate the total.

The app must not ask for or submit Beck answers, Beck total, the depression group, or student `Code`. Beck fields define the target; `Code` is an identifier.

## Candidate model inputs

The current broad model has 28 feature columns. For the first app-ready comparison, exclude `Average_Time_Use` from the primary set because its 1-3 hour category has only one observation in this dataset and the EDA flagged its coding for review. This leaves 27 candidate model fields:

| Form section | Model fields | Verified response mapping / UI treatment |
|---|---|---|
| Student/background | `Age`, `Semester`, `Department`, `Sex`, `MS`, `SES`, `Living_Arrangement`, `Residence_Area` | Use readable options from the dictionary. Department options are Law, Economics, Engineering and Health; they are specific to the source Colombian university. SES is the source dataset's six-level Colombian socioeconomic stratum. These fields cannot be assumed to transfer to another institution or country. |
| Family/phone context | `Family_Expression`, `Family_Activities`, `Mobile_Use_Rules`, `Phone_Discrimination`, `Phone_Related_Arguments`, `Subscription_Plan`, `Network _Access`, `Areas_Use`, `Type_MD`, `Time_First_Cellphone` | The first five use Never/Sometimes/Often/Always. Other fields use the categories in the source dictionary (for example prepaid/postpaid; cellular data/Wi-Fi/both; locations; device types; and time since first phone). Use human-readable labels, never show raw codes. |
| App-use flags | `Using_Text Messaging_Apps`, `Using_Games_Apps`, `Using_social media_Apps`, `Using_Music_Apps`, `Using_Videos_Apps`, `Using_Ttime-management_Apps`, `Using_Camara_Apps`, `Using_Mail_Apps` | UI can group these as app categories. The model encodes source No/Yes values (1/2) to 0/1 internally. The source dictionary and workbook have inconsistent spellings for some column names; use a mapping layer from friendly UI labels to the exact training column names. |
| Phone dependence | `TMD_Total_Recomputed` | Ask the 22 TMD items in two response-scale sections, then calculate the total in the app using the documented 0-4 item scoring. The model receives the total, not the 22 answers as separate features. |

The 27 model input fields translate to about 48 raw responses if the app asks one response per other field plus all 22 TMD questions. The TMD questions can be split into pages with progress feedback. Because this is a substantial form, compare a reduced input set before committing to the final UI.

## Feature selection and model comparison plan

1. Start with candidate features that the proposed app can ask, excluding identifiers and all depression/Beck fields.
2. Keep `Average_Time_Use` out of the primary candidate set; test it only as a sensitivity variant if its definition/coding is resolved.
3. The app-ready script compares the full 27-field candidate set with a reduced raw-field set. It aggregates L1 logistic-regression coefficients across one-hot categories back to original questionnaire fields, and refits selection within each CV training fold. The recalculated TMD total is always retained.
4. Compare logistic regression, decision tree, random forest and gradient boosting on the same input variants. Select by mean repeated training CV PR-AUC. The script evaluates the saved holdout only for the CV winner; this holdout has already been viewed in the broader-model work, so treat its metrics as preliminary.
5. The selected model only requires fields marked required in results/app_ready_model_inputs.csv. The separate L1-reduced candidate list is in results/app_ready_selected_fields.csv. The app must collect those fields, ask the 22 TMD questions, calculate TMD_Total_Recomputed and pass the resulting selected-field row to the model.

## Lecturer-demo output and integration

The result should state that it is a model estimate of the dataset-defined higher Beck-score group, not a diagnosis. Do not display an uncalibrated probability as personal certainty. Explain that the model was trained on questionnaire data from one Colombian university and has not been validated for other populations.

The lecturer demo should use the compact candidate for a shorter form: its 11 model fields are Department, SES, Living_Arrangement, Residence_Area, Areas_Use, Type_MD, Phone_Related_Arguments, Time_First_Cellphone, TMD_Total_Recomputed, Using_social media_Apps, and Using_Ttime-management_Apps. That means ten direct responses plus the 22 TMD responses used to calculate the total. Its CV PR-AUC was 0.262 versus 0.287 for the full-input Gradient Boosting model. The full model remains the highest-scoring comparison; the compact model is a usability tradeoff, not the overall performance winner. The holdout has already been reviewed, so its metrics are exploratory.

The Android app should send only the selected compact model inputs to a small Python service that loads the compact saved scikit-learn pipeline. The service returns the predicted score group, not a diagnosis. Do not show a personal probability until calibration and uncertainty are assessed. Kotlin cannot load the Python `joblib` model directly.

## Current status

- Depression is the sole prediction target; the separate dependence target has been dropped.
- The TMD total is retained as a predictor and will be calculated from 22 user answers.
- The source codebook gives the TMD item scales and dataset score bands; the Beck form/version still needs confirmation.
- The broad model uses 28 questionnaire features. The separate app-ready script compares 27 candidate fields with an L1-selected subset; its results are generated when run.
- The Android Studio project is a Jetpack Compose starter; it has no input form or model connection yet.
