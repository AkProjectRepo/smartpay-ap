"""
agent_workflow.py
-----------------
SmartPay AP - Main Agent Runner (D3)

Thin entry point. Builds graph and runs agent
for a given invoice ID.

All logic lives in:
    state.py          - InvoiceState definition
    knowledge_base.py - Vendor contracts, history, policy
    rag.py            - RAG lookup logic
    matching_tool.py  - D2 matching model as tool
    email_drafter.py  - LLM email drafting
    nodes.py          - All 7 LangGraph nodes
    graph.py          - Graph structure and routing

Why thin:
    Main runner should only orchestrate.
    Easy to swap graph implementation later.
    Easy to add CLI arguments or API wrapper.
"""

import os
import sys
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# Add src to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import InvoiceState
from graph import build_graph
from nodes import (
    node_load_invoice,
    node_guardrail,
    node_match,
    node_rag_lookup,
    node_draft_email,
    node_human_approval,
    node_execute,
    node_auto_approve,
)

BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(BASE_DIR, "data")
LABELED_FILE = os.path.join(DATA_DIR, "labeled_dataset.csv")


def run_agent(invoice_id: str) -> dict:
    """
    Run SmartPay AP agent for a given invoice.

    Args:
        invoice_id: e.g. "INV0002"

    Returns:
        Final InvoiceState after workflow completes
    """
    print("=" * 60)
    print("  SmartPay AP - Agentic Reconciliation Workflow (D3)")
    print("=" * 60)
    print(f"  Processing Invoice: {invoice_id}")
    print("=" * 60)

    # Initial state
    initial_state: InvoiceState = {
        "invoice_id":        invoice_id,
        "invoice_total":     0.0,
        "vendor_name":       "",
        "invoice_lines":     [],
        "guardrail_blocked": False,
        "match_result":      "",
        "mismatches":        [],
        "match_summary":     "",
        "rag_context":       {},
        "email_draft":       "",
        "human_decision":    "",
        "final_status":      "",
    }

    # Try LangGraph first
    graph = build_graph()

    if graph:
        print("\n[INFO] Running with LangGraph\n")
        final_state = graph.invoke(initial_state)
    else:
        # Manual fallback execution
        print("\n[INFO] Running manual workflow\n")
        state = initial_state
        state = node_load_invoice(state)
        state = node_guardrail(state)

        if not state["guardrail_blocked"]:
            state = node_match(state)

            if state["match_result"] == "MISMATCH":
                state = node_rag_lookup(state)
                state = node_draft_email(state)
                state = node_human_approval(state)
                state = node_execute(state)
            else:
                state = node_auto_approve(state)

        final_state = state

    # Final summary
    print("\n" + "=" * 60)
    print("  FINAL STATUS")
    print("=" * 60)
    print(f"  {final_state['final_status']}")
    print("=" * 60)

    return final_state


if __name__ == "__main__":
    try:
        df = pd.read_csv(LABELED_FILE)

        # Find a mismatch invoice to demo
        mismatch_invoice = df[
            df["is_mismatch"] == 1
        ]["invoice_id"].iloc[0]

        print(f"\nDemo invoice: {mismatch_invoice}")
        run_agent(mismatch_invoice)

    except FileNotFoundError:
        print("labeled_dataset.csv not found.")
        print("Run D2 notebook first to generate the dataset.")
