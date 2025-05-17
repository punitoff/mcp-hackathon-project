"""CLI entry for quick manual testing."""
import argparse
from summarization.generate import main as run_summary


def parse_args():
    parser = argparse.ArgumentParser(description="Run summary and alerts generator")
    parser.add_argument("patient_id", help="Synthetic patient ID (without .json)")
    return parser.parse_args()


def main():
    args = parse_args()
    run_summary(args.patient_id)


if __name__ == "__main__":
    main()
