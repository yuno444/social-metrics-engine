"""Instagram performance dashboard.

Run with: streamlit run app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data.csv"
SAMPLE_PATH = BASE_DIR / "sample_data.csv"

ENGAGEMENT_COLS = ["Likes", "Comments", "Reposts", "Shares", "Saves"]
BRAND_COL = "Primary Watch Brands"

# Values in the brand column that mean "no brand featured".
BRAND_NULLS = {"", "na", "n/a", "none", "nan", "-", "null"}

st.set_page_config(
    page_title="Instagram Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {padding-top: 2.5rem; padding-bottom: 3rem;}
        [data-testid="stMetric"] {
            background: #ffffff0d;
            border: 1px solid #ffffff1a;
            border-radius: 0.75rem;
            padding: 1rem 1.25rem;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            opacity: 0.7;
        }
        #MainMenu, footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)


def find_data_file() -> tuple[Path | None, bool]:
    """Locate the data file, falling back to the bundled sample.

    Spreadsheet exports often arrive as `data(Sheet1).csv`, so any `data*.csv`
    counts. Returns (path, is_sample); path is None when nothing is found.
    """
    if DATA_PATH.exists():
        return DATA_PATH, False
    candidates = sorted(p for p in BASE_DIR.glob("data*.csv") if p != SAMPLE_PATH)
    if candidates:
        return candidates[0], False
    if SAMPLE_PATH.exists():
        return SAMPLE_PATH, True
    return None, False


def read_table(path: Path) -> pd.DataFrame:
    """Read a CSV whose header may sit below leading blank spacer rows."""
    probe = pd.read_csv(path, header=None, nrows=15, dtype=str)
    header_row = 0
    for i in range(len(probe)):
        if probe.iloc[i].astype(str).str.strip().eq("Post Date").any():
            header_row = i
            break

    df = pd.read_csv(path, header=header_row)
    df.columns = [str(c).strip() for c in df.columns]

    # Excel exports pad the sheet with empty spacer rows and columns.
    blank_cols = [
        c for c in df.columns if c.startswith("Unnamed:") and df[c].isna().all()
    ]
    return df.drop(columns=blank_cols).dropna(how="all")


def parse_dates(series: pd.Series) -> pd.Series:
    """Parse dates as US month-first, falling back to mixed formats."""
    parsed = pd.to_datetime(series, format="%m/%d/%Y", errors="coerce")
    unparsed = parsed.isna() & series.notna()
    if unparsed.any():
        parsed.loc[unparsed] = pd.to_datetime(
            series[unparsed], format="mixed", dayfirst=False, errors="coerce"
        )
    return parsed


@st.cache_data(show_spinner="Loading data…")
def load_data(path: Path) -> pd.DataFrame:
    """Read the CSV, coerce types, engineer metrics, and sort chronologically."""
    df = read_table(path)

    missing = [c for c in ["Post Date", "Views", *ENGAGEMENT_COLS] if c not in df.columns]
    if missing:
        raise ValueError(f"{path.name} is missing required column(s): {', '.join(missing)}")

    df["Post Date"] = parse_dates(df["Post Date"])
    df = df.dropna(subset=["Post Date"])

    for col in ["Views", *ENGAGEMENT_COLS]:
        # Strip thousands separators that Instagram exports sometimes include.
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(r"[,\s]", "", regex=True), errors="coerce"
        ).fillna(0)

    df["Total Engagement"] = df[ENGAGEMENT_COLS].sum(axis=1)
    # Posts with 0 views have no meaningful rate, so leave them as NaN rather than inf.
    df["Engagement Rate"] = df["Total Engagement"] / df["Views"].replace(0, np.nan)

    if BRAND_COL not in df.columns:
        df[BRAND_COL] = pd.NA

    return df.sort_values("Post Date").reset_index(drop=True)


def explode_brands(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (post, brand), dropping posts with no brand tagged."""
    brands = df[BRAND_COL].astype("string")
    exploded = (
        df.assign(Brand=brands.str.split(","))
        .dropna(subset=["Brand"])
        .explode("Brand")
    )
    exploded["Brand"] = exploded["Brand"].str.strip()
    return exploded[~exploded["Brand"].str.lower().isin(BRAND_NULLS)]


def fmt_compact(value: float) -> str:
    """Format a number as 1.2K / 3.4M for KPI display."""
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs(value) >= threshold:
            return f"{value / threshold:,.1f}{suffix}"
    return f"{value:,.0f}"


active_path, using_sample = find_data_file()

if active_path is None:
    st.title("📊 Instagram Analytics")
    st.error(f"Couldn't find `data.csv` in `{BASE_DIR}`.")
    st.caption(
        "Expected columns: Post Date, Views, Likes, Comments, Reposts, Shares, Saves, "
        "Primary Watch Brands."
    )
    st.stop()

try:
    data = load_data(active_path)
except (ValueError, pd.errors.ParserError) as exc:
    st.title("📊 Instagram Analytics")
    st.error(str(exc))
    st.stop()

if data.empty:
    st.title("📊 Instagram Analytics")
    st.warning("No rows with a valid `Post Date` were found in data.csv.")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────

min_date = data["Post Date"].min().date()
max_date = data["Post Date"].max().date()

with st.sidebar:
    st.header("Filters")
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD",
    )

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:  # user has only clicked the first date so far
        start_date = end_date = (
            date_range[0] if isinstance(date_range, (list, tuple)) else date_range
        )

    granularity = st.selectbox("Time-series grouping", ["Day", "Week", "Month"], index=2)
    log_scale = st.toggle(
        "Log scale",
        help="Useful when a single viral post flattens the rest of the chart.",
    )
    top_n = st.slider("Brands to rank", min_value=3, max_value=25, value=10)
    min_posts = st.number_input(
        "Min. posts per brand",
        min_value=1,
        value=1,
        help="Hide brands with too few posts to be meaningful.",
    )

range_start = pd.Timestamp(start_date)
range_end = pd.Timestamp(end_date) + pd.Timedelta(days=1)  # include the whole end day
df = data.loc[
    (data["Post Date"] >= range_start) & (data["Post Date"] < range_end)
]

st.title("📊 Instagram Analytics")
if using_sample:
    st.info("Showing `sample_data.csv` — drop your own `data.csv` in this folder to use real data.")
st.caption(
    f"{start_date:%b %d, %Y} → {end_date:%b %d, %Y} · {len(df):,} posts "
    f"of {len(data):,} total · source: `{active_path.name}`"
)

if df.empty:
    st.warning("No posts in the selected date range.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────

total_views = df["Views"].sum()
total_engagement = df["Total Engagement"].sum()
avg_engagement_rate = df["Engagement Rate"].mean()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Views", fmt_compact(total_views))
k2.metric(
    "Avg Engagement Rate",
    f"{avg_engagement_rate:.2%}" if pd.notna(avg_engagement_rate) else "—",
)
k3.metric("Total Engagement", fmt_compact(total_engagement))
k4.metric("Avg Views / Post", fmt_compact(df["Views"].mean()))

st.divider()

# ── Time series ───────────────────────────────────────────────────────────────

freq = {"Day": "D", "Week": "W-MON", "Month": "MS"}[granularity]
timeline = (
    df.set_index("Post Date")
    .resample(freq)[["Views", "Total Engagement"]]
    .sum()
    .reset_index()
)

fig_time = make_subplots(specs=[[{"secondary_y": True}]])
fig_time.add_trace(
    go.Scatter(
        x=timeline["Post Date"],
        y=timeline["Views"],
        name="Views",
        mode="lines+markers",
        line=dict(color="#6366f1", width=2.5),
        hovertemplate="%{x|%b %d, %Y}<br>Views: %{y:,.0f}<extra></extra>",
    ),
    secondary_y=False,
)
fig_time.add_trace(
    go.Scatter(
        x=timeline["Post Date"],
        y=timeline["Total Engagement"],
        name="Total Engagement",
        mode="lines+markers",
        line=dict(color="#f59e0b", width=2.5),
        hovertemplate="%{x|%b %d, %Y}<br>Engagement: %{y:,.0f}<extra></extra>",
    ),
    secondary_y=True,
)
axis_type = "log" if log_scale else "linear"
fig_time.update_yaxes(
    title_text="Views",
    type=axis_type,
    secondary_y=False,
    showgrid=True,
    gridcolor="rgba(128,128,128,0.2)",
)
fig_time.update_yaxes(
    title_text="Total Engagement", type=axis_type, secondary_y=True, showgrid=False
)
fig_time.update_layout(
    title=f"Views & engagement over time ({granularity.lower()}ly)",
    hovermode="x unified",
    margin=dict(l=10, r=10, t=60, b=10),
    height=430,
    legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1),
)
st.plotly_chart(fig_time, width="stretch")

# ── Brand ranking ─────────────────────────────────────────────────────────────

brand_df = explode_brands(df)

if brand_df.empty:
    st.info("No brands tagged on posts in this date range.")
else:
    brand_stats = (
        brand_df.groupby("Brand")
        .agg(
            Posts=("Views", "size"),
            **{
                "Avg Views": ("Views", "mean"),
                "Total Views": ("Views", "sum"),
                "Avg Engagement": ("Total Engagement", "mean"),
                "Avg Engagement Rate": ("Engagement Rate", "mean"),
            },
        )
        .reset_index()
    )
    brand_stats = brand_stats[brand_stats["Posts"] >= min_posts]

    if brand_stats.empty:
        st.info(f"No brands with at least {min_posts} post(s) in this date range.")
    else:
        ranked = brand_stats.nlargest(top_n, "Avg Views").sort_values("Avg Views")

        fig_brand = px.bar(
            ranked,
            x="Avg Views",
            y="Brand",
            orientation="h",
            color="Avg Views",
            color_continuous_scale=["#c7d2fe", "#818cf8", "#4338ca"],
            custom_data=["Posts", "Avg Engagement Rate"],
        )
        fig_brand.update_traces(
            hovertemplate=(
                "<b>%{y}</b><br>Avg views: %{x:,.0f}<br>"
                "Posts: %{customdata[0]}<br>"
                "Avg engagement rate: %{customdata[1]:.2%}<extra></extra>"
            )
        )
        fig_brand.update_layout(
            title=f"Top {len(ranked)} watch brands by average views",
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=60, b=10),
            height=max(380, 34 * len(ranked) + 120),
            xaxis_title="Average views per post",
            yaxis_title=None,
        )
        st.plotly_chart(fig_brand, width="stretch")

        with st.expander("Brand breakdown table"):
            table = brand_stats.sort_values("Avg Views", ascending=False).copy()
            table["Avg Engagement Rate"] *= 100
            st.dataframe(
                table,
                width="stretch",
                hide_index=True,
                column_config={
                    "Avg Views": st.column_config.NumberColumn(format="%.0f"),
                    "Total Views": st.column_config.NumberColumn(format="%.0f"),
                    "Avg Engagement": st.column_config.NumberColumn(format="%.0f"),
                    "Avg Engagement Rate": st.column_config.NumberColumn(format="%.2f%%"),
                },
            )

with st.expander("Post-level data"):
    posts = df.sort_values("Post Date", ascending=False).copy()
    posts["Engagement Rate"] *= 100
    st.dataframe(
        posts,
        width="stretch",
        hide_index=True,
        column_config={
            "Post Date": st.column_config.DatetimeColumn(format="YYYY-MM-DD"),
            "Engagement Rate": st.column_config.NumberColumn(format="%.2f%%"),
        },
    )
