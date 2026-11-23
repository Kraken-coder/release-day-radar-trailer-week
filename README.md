# Trailer Week → Opening Weekend

**Question:** Does trailer-week YouTube engagement predict opening-weekend collections across Hindi and regional releases?

Across **15 eligible films from 2025**, surviving trailer-week comment volume has a Spearman correlation of **0.78** with opening-weekend India nett. However, adding comments to a Hindi/regional baseline increased mean absolute error on four later releases from **INR 17.16 crore to INR 24.78 crore**. RMSE and leave-one-out checks are more favourable: the evidence depends on the metric and split, and does not establish a reliable forecasting rule.

Engagement means timestamped comments in an official trailer’s first seven days, ending before release. Historical views and likes are unavailable from current API counters. The target is Friday–Sunday, all-language India nett in INR crores. Comment survival and selection of a single official upload limit the study.

- [Executed analysis notebook](project/src/trailer_week_radar.ipynb)
- [Setup, sources and methodology](project/src/README.md)
- [Eligible film-level data](project/data/clean/model_data.csv)
- [Holdout predictions](project/data/results/holdout_predictions.csv)
- [Cleaning log](project/data/results/cleaning_log.csv)

Code lives in `project/src`; inputs and outputs live in `project/data`. The separate sentiment/aspect project remains independent. No API key or database files are versioned.
