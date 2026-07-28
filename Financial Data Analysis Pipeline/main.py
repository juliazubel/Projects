"""
main.py
-------
Orchestrates the full Financial Data Analysis Pipeline.

Usage:
    python main.py
    python main.py --file data/transactions.csv
    python main.py --generate
    python main.py --generate --no-plots
"""

import argparse
import logging
import runpy
import sys
from pathlib import Path

# ── Paths setup ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
DEFAULT_REPORT_DIR = BASE_DIR / "reports"

# Add src/ to Python path
sys.path.insert(0, str(SRC_DIR))

# Imports (must come after the sys.path tweak above)
from analysis import (  # noqa: E402
    anomaly_report,
    category_breakdown,
    compute_kpis,
    department_analysis,
    monthly_trend,
    regional_analysis,
)
from data_cleaning import clean_data, load_data  # noqa: E402
from visualization import generate_report  # noqa: E402

log = logging.getLogger("pipeline")


# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(filepath: Path, report_dir: Path, make_plots: bool = True) -> None:
    print("\n" + "=" * 60)
    print("  FINANCIAL DATA ANALYSIS PIPELINE")
    print("=" * 60)

    # 1. LOAD ─────────────────────────────────────────────────────────────────
    print("\n[1/5] Loading data …")
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset not found: {filepath.resolve()}")

    df_raw = load_data(filepath)
    if df_raw.empty:
        raise ValueError(f"'{filepath}' contains no rows — nothing to analyse.")

    # 2. CLEAN ────────────────────────────────────────────────────────────────
    print("[2/5] Cleaning data …")
    df, cleaning_report = clean_data(df_raw)
    print(f"      → Rows after cleaning: {len(df):,}")

    for step, val in cleaning_report.items():
        print(f"      {step}: {val}")

    if df.empty:
        raise ValueError(
            "All rows were removed during cleaning — check the input data quality."
        )

    # 3. ANALYSE ──────────────────────────────────────────────────────────────
    print("[3/5] Running analysis …")
    kpis = compute_kpis(df)
    trend = monthly_trend(df)
    cat_df = category_breakdown(df)
    regional = regional_analysis(df)
    dept = department_analysis(df)
    anomalies = anomaly_report(df)

    # Print KPIs
    print("\n  ── KPI Summary ─────────────────────────────────")
    for k, v in kpis.items():
        label = k.replace("_", " ").title()
        print(f"  {label:<25} {v}")

    # Print anomalies
    if not anomalies.empty:
        print(f"\n  ── Top Anomalies (showing 5 of {len(anomalies)}) ──────────")
        print(anomalies.head(5).to_string(index=False))

    # 4. SAVE CSV RESULTS ─────────────────────────────────────────────────────
    print("\n[4/5] Saving result tables …")
    report_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(report_dir / "clean_data.csv", index=False)
    trend.to_csv(report_dir / "monthly_trend.csv", index=False)
    cat_df.to_csv(report_dir / "category_breakdown.csv", index=False)
    dept.to_csv(report_dir / "department_analysis.csv", index=False)

    if not anomalies.empty:
        anomalies.to_csv(report_dir / "anomalies.csv", index=False)

    print(f"      → CSVs written to {report_dir}")

    # 5. VISUALISE ────────────────────────────────────────────────────────────
    outputs = [
        report_dir / "clean_data.csv",
        report_dir / "monthly_trend.csv",
        report_dir / "category_breakdown.csv",
        report_dir / "department_analysis.csv",
    ]
    if not anomalies.empty:
        outputs.append(report_dir / "anomalies.csv")

    if make_plots:
        print("[5/5] Generating visualisations …")
        generate_report(
            df=df,
            trend=trend,
            cat_df=cat_df,
            regional_df=regional,
            kpis=kpis,
            output_path=report_dir / "results.png",
        )
        outputs += [report_dir / "results.png", report_dir / "mom_growth.png"]
    else:
        print("[5/5] Skipping visualisations (--no-plots)")

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print("  Outputs:")
    for path in outputs:
        print(f"    {path}")
    print("=" * 60 + "\n")


# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Financial Data Analysis Pipeline")

    parser.add_argument(
        "--file",
        default=str(DATA_DIR / "transactions.csv"),
        help="Path to input CSV (default: data/transactions.csv)",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate synthetic demo data before running",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_REPORT_DIR),
        help="Directory to write CSV/PNG outputs to (default: reports/)",
    )
    parser.add_argument(
        "--no-plots",
        action="store_true",
        help="Skip chart generation and only write CSV outputs",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug-level logging",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s | %(name)s | %(message)s",
    )

    if args.generate:
        print("Generating synthetic dataset …")
        runpy.run_path(str(DATA_DIR / "generate_data.py"))

    try:
        run_pipeline(
            filepath=Path(args.file),
            report_dir=Path(args.output_dir),
            make_plots=not args.no_plots,
        )
    except (FileNotFoundError, ValueError) as exc:
        log.error(str(exc))
        print(f"\n✗ Pipeline failed: {exc}\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
