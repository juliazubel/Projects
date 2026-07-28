# Financial Data Analysis Pipeline

> End-to-end Python pipeline for financial transaction analysis — data cleaning, feature engineering, anomaly detection, and automated report generation.

[![CI](https://github.com/juliazubel/Projects/actions/workflows/financial-data-analysis-pipeline.yml/badge.svg)](https://github.com/juliazubel/Projects/actions/workflows/financial-data-analysis-pipeline.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)

---

## Quick Start

```bash
# 1. Clone the repo and set up a virtual environment
cd "Financial Data Analysis Pipeline"
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Generate demo data and run the full pipeline
python main.py --generate

# 3. Or point it at your own CSV
python main.py --file path/to/your/data.csv
```

Outputs land in `reports/` — open `results.png` for the full dashboard.

Useful flags: `--output-dir <path>` to change where results are written, `--no-plots` to skip chart rendering (CSV-only, fast), `-v/--verbose` for debug logging.

---

## Project Structure

```
Financial Data Analysis Pipeline/
├── data/
│   ├── generate_data.py       # Synthetic dataset generator (2 years, 2 000 rows)
│   └── transactions.csv       # Generated demo dataset
│
├── src/
│   ├── data_cleaning.py       # Schema validation, null handling, anomaly flagging
│   ├── analysis.py            # KPIs, monthly trend, regional & dept breakdowns
│   └── visualization.py       # All matplotlib charts + dashboard renderer
│
├── reports/                   # Pipeline outputs (auto-created)
│   ├── results.png            ← Main 5-panel dashboard
│   ├── mom_growth.png         ← Month-over-month revenue growth
│   ├── clean_data.csv
│   ├── monthly_trend.csv
│   ├── category_breakdown.csv
│   ├── department_analysis.csv
│   └── anomalies.csv
│
├── tests/                     # pytest unit tests for cleaning & analysis
├── main.py                    # Pipeline orchestrator (CLI entry point)
├── requirements.txt
├── requirements-dev.txt       # + pytest, ruff
├── pyproject.toml             # ruff/pytest config
└── README.md
```

---

## What the Pipeline Does

### 1 · Data Cleaning (`src/data_cleaning.py`)

| Step | Technique |
|---|---|
| Schema validation | Raises on missing required columns |
| Null handling | Drops rows with null `amount`; fills categorical nulls with `"Unknown"` |
| Deduplication | Unique `transaction_id` enforcement |
| Type coercion | Numeric casting + explicit truthy-set boolean mapping (avoids the classic `bool(NaN) == True` trap) |
| Anomaly flagging | **IQR method** (3× fence) per category → `is_anomaly` column |
| Feature engineering | `year`, `month`, `quarter`, `weekday`, `is_weekend` |

### 2 · Analysis (`src/analysis.py`)

- **KPI summary** — total revenue, expenses, net cash flow, approval rate
- **Monthly trend** — absolute totals + MoM % growth + 3-month rolling average
- **Category breakdown** — sum, mean, count, std per transaction type
- **Regional analysis** — pivot table + true transaction volume (sum of absolute amounts) per region
- **Department analysis** — financials per department with anomaly counts
- **Anomaly report** — flagged transactions with Z-scores, sorted by severity

### 3 · Visualisation (`src/visualization.py`)

Five charts in a single dark-theme dashboard, plus a separate MoM growth chart:

| Chart | Insight |
|---|---|
| Monthly Revenue vs Expenses | Trend over time with rolling average |
| Cumulative Net Cash Flow | Running total with +/- colour fill |
| Category Donut | Distribution of transaction types |
| Anomaly Scatter | All transactions; anomalies highlighted in red |
| Regional Volume | Horizontal bar chart by region |
| MoM Growth | Month-over-month revenue % change (separate file) |

---

## Testing

```bash
pip install -r requirements-dev.txt
pytest         # 17 unit tests covering data_cleaning.py and analysis.py
ruff check .   # lint
```

CI runs both on every push via [GitHub Actions](../.github/workflows/financial-data-analysis-pipeline.yml), across Python 3.10–3.12, and also executes the pipeline end-to-end (`--generate`) to catch regressions that unit tests alone would miss.

---

## Stack

| Library | Version | Role |
|---|---|---|
| `pandas` | ≥ 2.0 | Data wrangling, aggregations |
| `numpy` | ≥ 1.24 | Statistical calculations |
| `matplotlib` | ≥ 3.7 | All visualisations |
| `pytest` | ≥ 8.0 | Test suite |
| `ruff` | ≥ 0.6 | Linting |

---

## Example Output

After running `python main.py --generate`:

```
══════════════════════════════════════════════════════════
  FINANCIAL DATA ANALYSIS PIPELINE
══════════════════════════════════════════════════════════

[1/5] Loading data …        INFO | Loaded 2000 rows × 7 columns
[2/5] Cleaning data …       INFO | Removed 40 rows with null 'amount'
                            INFO | Anomalies flagged: 47
[3/5] Running analysis …

  ── KPI Summary ─────────────────────────────────
  Total Transactions        1,960
  Total Revenue         $21,267,907
  Total Expenses         -$6,076,937
  Net Cashflow           $15,190,971
  Anomaly Count                  47
  Anomaly Pct                  2.4%
  Approval Rate               92.5%

[4/5] Saving result tables …
[5/5] Generating visualisations …
  ✓ Dashboard saved  → reports/results.png
  ✓ MoM growth chart → reports/mom_growth.png
```

---

## Design Notes

A few deliberate calls worth flagging for reviewers:

- **Booleans are mapped explicitly, not `.astype(bool)`'d.** Pandas' bare cast treats `NaN` and the string `"False"` as truthy, which would silently mark unapproved/missing transactions as approved. The cleaning step uses an explicit truthy set instead.
- **"Regional volume" is `sum(abs(amount))`, not `abs(sum(amount))`.** The latter lets revenue and expenses cancel out and can understate a region's actual activity — a net-zero region isn't necessarily an idle one.
- **Chart styling is applied in two layers.** `_apply_dark_style()` only sets shared chrome (colors, ticks, spines); each `plot_*` function owns its own axis formatters. An earlier version applied a blanket dollar-formatter to every y-axis, which silently overwrote the regional bar chart's category labels with `$0`–`$4`.
