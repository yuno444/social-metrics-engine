# Instagram Analytics Dashboard

A Streamlit dashboard for exploring Instagram post performance: views, engagement, and which watch brands drive the most reach.

Built with **Python**, **Pandas**, and **Plotly**.

## Features

- Load CSV exports (including Excel-style sheets with extra blank rows/columns)
- **Total Engagement** and **Engagement Rate** per post
- Split comma-separated **Primary Watch Brands** for per-brand rankings
- Sidebar filters: date range, time grouping, top-N brands, minimum posts per brand
- Interactive charts: views & engagement over time, top brands by average views
- Expandable tables for brand breakdown and post-level data

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

- **Sparse posting:** Use **Month** grouping in the sidebar for clearer trends.
- **Viral posts:** Turn on **Log scale** when one post dominates the chart.
- **Brand names:** Inconsistent labels (e.g. `Patek` vs `Patek Philippe`) appear as separate brands until you normalize them in the CSV.

## License

Private project — use and modify as you like.
