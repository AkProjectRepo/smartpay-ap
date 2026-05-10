"""
run.py
------
SmartPay AP - Simple Runner

Usage:
    python run.py              # runs with demo mismatch invoice
    python run.py INV0002      # runs with specific invoice
    python run.py INV0001      # runs with clean invoice
"""

import sys
import os
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from agent_workflow import run_agent

DATA_DIR     = os.path.join(os.path.dirname(__file__), "data")
LABELED_FILE = os.path.join(DATA_DIR, "labeled_dataset.csv")

if __name__ == "__main__":
    # If invoice ID passed as argument use it
    # Otherwise find first mismatch invoice automatically
    if len(sys.argv) > 1:
        invoice_id = sys.argv[1]
    else:
        try:
            df         = pd.read_csv(LABELED_FILE)
            invoice_id = df[df["is_mismatch"] == 1]["invoice_id"].iloc[0]
            print(f"No invoice specified. Using: {invoice_id}\n")
        except FileNotFoundError:
            print("labeled_dataset.csv not found.")
            print("Run D2 notebook first.")
            sys.exit(1)

    run_agent(invoice_id)
