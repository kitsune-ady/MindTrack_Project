# Presentation wording: depression score-group target

## What the model predicts

The model predicts whether the participant’s Beck total is **below 11** or **11 and above**. The project defines the positive class as Beck total ≥11. This combines the codebook’s 11–16 “mild mood disturbance” band with every higher score band, including 17–20 and above.

## Say this

> “Our model predicts whether a participant’s Beck questionnaire score falls below 11 or in the 11-and-above group. The positive group includes several score bands, starting with mild mood disturbance. This is a research classification of questionnaire scores, not a clinical diagnosis.”

## If asked, “Does 17+ count too?”

> “Yes. Under our current binary target, every score from 11 upward receives the same positive label. The model does not distinguish 11–16 from 17+ or from the higher score bands.”

## Important qualification

The files use potentially inconsistent Beck-version wording. Confirm with the lecturer that the questionnaire and scoring guide correspond before describing the 11+ grouping as a depression classification. If the lecturer chooses a different threshold or wants separate score bands, redefine the target and rerun the analysis. Do not call the model diagnostic or claim it proves that phone use causes depression.
