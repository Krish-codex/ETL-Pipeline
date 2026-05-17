"""
Main Pipeline Orchestrator
===========================
This is the entry point for the entire ETL pipeline.

It runs all steps in sequence:
  1. Extract  — Fetch weather data from OpenWeather API
  2. Transform — Clean and structure the raw data
  3. Load     — Insert cleaned data into MySQL
  4. Analyze  — Run SQL queries and generate reports

Usage:
    python main.py           (runs full pipeline)
    python main.py --step 1  (runs only extraction)
    python main.py --step 2  (runs only transformation)
    python main.py --step 3  (runs only loading)
    python main.py --step 4  (runs only analysis)

"""

import argparse
import sys
import time
from datetime import datetime

# Configure Windows terminal to print Unicode characters and Emojis properly
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from scripts.fetch_data import run_extraction
from scripts.clean_data import run_transformation
from scripts.load_to_mysql import run_loading
from scripts.analyze_data import run_analysis
from scripts.logger_setup import get_logger

# Initialize logger for the main module
logger = get_logger("main")

BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🌦️  AUTOMATED ETL PIPELINE - Weather Data                ║
║       ─────────────────────────────────────                  ║
║   Extract  →  Transform  →  Load  →  Analyze                 ║
║                                                              ║
║   Tech: Python • MySQL • Pandas • OpenWeather API            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def run_pipeline_step(step_name: str, step_func, step_num: int) -> bool:
    """
    Runs a single pipeline step with timing and status tracking.

    Args:
        step_name: Human-readable name of the step
        step_func: The function to execute for this step
        step_num: Step number (1-4)

    Returns:
        True if the step succeeded, False otherwise
    """
    logger.info(f"\n{'━' * 60}")
    logger.info(f"  PIPELINE STEP {step_num}: {step_name}")
    logger.info(f"{'━' * 60}")

    start_time = time.time()

    try:
        success = step_func()
        elapsed = time.time() - start_time

        if success:
            logger.info(f"✅ {step_name} completed in {elapsed:.2f}s")
        else:
            logger.error(f"❌ {step_name} failed after {elapsed:.2f}s")

        return success

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ {step_name} crashed after {elapsed:.2f}s: {e}")
        return False


def run_full_pipeline() -> bool:
    """
    Executes the complete ETL pipeline end-to-end.

    Returns:
        True if all steps succeeded, False if any step failed

    The pipeline stops if any step fails — there's no point
    trying to load data into MySQL if the extraction failed.
    """
    print(BANNER)
    logger.info(f"Pipeline started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    pipeline_start = time.time()

    # Define pipeline steps in execution order
    steps = [
        ("Data Extraction (API Fetch)", run_extraction, 1),
        ("Data Transformation (Clean & Structure)", run_transformation, 2),
        ("Database Loading (CSV → MySQL)", run_loading, 3),
        ("SQL Analysis (Generate Reports)", run_analysis, 4),
    ]

    results = {}
    all_passed = True

    for step_name, step_func, step_num in steps:
        success = run_pipeline_step(step_name, step_func, step_num)
        results[step_name] = "✅ PASS" if success else "❌ FAIL"

        if not success:
            all_passed = False
            logger.error(f"Pipeline stopped at Step {step_num} due to failure.")
            break

    # Print pipeline summary
    total_time = time.time() - pipeline_start
    logger.info(f"\n{'═' * 60}")
    logger.info("  PIPELINE EXECUTION SUMMARY")
    logger.info(f"{'═' * 60}")
    for step, status in results.items():
        logger.info(f"  {status}  {step}")
    logger.info(f"{'─' * 60}")
    logger.info(f"  Total time: {total_time:.2f}s")
    logger.info(f"  Status: {'ALL STEPS PASSED ✅' if all_passed else 'PIPELINE FAILED ❌'}")
    logger.info(f"{'═' * 60}\n")

    return all_passed


def run_single_step(step_num: int) -> bool:
    """Runs a specific pipeline step by its number."""
    step_map = {
        1: ("Data Extraction", run_extraction),
        2: ("Data Transformation", run_transformation),
        3: ("Database Loading", run_loading),
        4: ("SQL Analysis", run_analysis),
    }

    if step_num not in step_map:
        logger.error(f"Invalid step number: {step_num}. Use 1-4.")
        return False

    name, func = step_map[step_num]
    return run_pipeline_step(name, func, step_num)


def main():
    """Entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Automated ETL Pipeline — Weather Data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python main.py          Run full pipeline\n  python main.py --step 1  Run only extraction",
    )
    parser.add_argument(
        "--step", type=int, choices=[1, 2, 3, 4],
        help="Run a specific step (1=Extract, 2=Transform, 3=Load, 4=Analyze)",
    )

    args = parser.parse_args()

    if args.step:
        success = run_single_step(args.step)
    else:
        success = run_full_pipeline()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
