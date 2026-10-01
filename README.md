# Social Metrics Engine: Interactive Analytics Dashboard

## Overview

An interactive web application engineered to parse raw CSV exports of social media metrics into actionable business intelligence. This dashboard ingests raw engagement data, normalizes date and string formats, and generates dynamic time-series visualizations to track content performance and audience conversion rates over time.

## Key Features

- **Automated KPI Generation:** Dynamically computes high-level metrics including Total Views, Average Engagement Rate, and Total Engagement across 31 individual records.

- **Granular Data Filtering:** Implements interactive sidebar controls allowing users to isolate data by custom date ranges (spanning from October 2024 to September 2026), adjust time-series grouping, and toggle minimum post thresholds.

- **Advanced String Parsing:** Utilizes Pandas data manipulation to clean and explode multi-variable data cells. This allows the engine to accurately isolate and calculate metrics for individual brands (such as Rolex, Seiko, and Grand Seiko) even when they are tagged together in a single post.

- **Interactive Data Visualization:** Integrates Plotly to render time-series line charts tracking view and engagement spikes, alongside bar charts ranking the top 10 watch brands by average views.

- **Post-Level Auditing:** Features a sortable, calculated dataframe view to inspect raw metrics and computed engagement rates down to the individual post level, handling single posts with up to 549,583 views and 11,733 total engagements.

## Technical Stack

- **Language:** Python
- **Data Processing:** Pandas
- **Frontend/Framework:** Streamlit
- **Data Visualization:** Plotly

## Business Value

Designed to bridge the gap between raw marketing data and strategic decision-making. By calculating total engagement rates (Likes + Comments + Reposts + Shares + Saves / Views) and breaking down performance by specific product categories (e.g., Grand Seiko achieving a 5.36% engagement rate versus Rolex at 2.99%), this tool identifies the exact variables that drive algorithmic reach and user conversion.

## Quick start

**Requirements:** Python 3.10+

```powershell
cd "IG Analytics"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`).

## Data file

Place your export in this folder as **`data.csv`**, or any name matching **`data*.csv`** (for example `data(Sheet1).csv`). If no data file is found, the app uses **`sample_data.csv`**.

Expected columns:

| Column | Description |
|--------|-------------|
| Post Date | Post date (`M/D/YYYY` or ISO) |
| Views | View count |
| Likes, Comments, Reposts, Shares, Saves | Engagement metrics |
| Primary Watch Brands | One or more brands, comma-separated; `NA` / empty = no brand |

## Project layout

```
app.py              # Streamlit app
requirements.txt    # Dependencies
sample_data.csv     # Demo dataset
README.md
```

## Tips

- **Sparse Posts:** Use **Month** grouping in the sidebar for clearer trends.
- **Viral posts:** Turn on **Log scale** when one post dominates the chart.

## License

Private project — use and modify as you like.
