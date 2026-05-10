"""
nodes.py
--------
SmartPay AP - LangGraph Node Functions

All 7 agent nodes defined here.
Each node takes InvoiceState and returns InvoiceState.

Why separate file:
    Single responsibility — only node logic.
    Imports from matching_tool, rag, email_drafter.
    graph.py imports from here.
"""

import pandas as pd
from state import InvoiceState
from matching_tool import matching_tool
from rag import rag_lookup
from email_drafter import draft_email

import os
BASE_DIR     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(BASE_DIR, "data")
LABELED_FILE = os.path.join(DATA_DIR, "labeled_dataset.csv")

HIGH_VALUE_THRESHOLD = 50_000.00


def node_load_invoice(state: InvoiceState) -> InvoiceState:
    """
    Node 1: Load invoice details from dataset.
    In production: fetches from SAP/Oracle via API.
    """
    print(f"\n[NODE 1] Loading invoice {state['invoice_id']}...")

    try:
        df   = pd.read_csv(LABELED_FILE)
        rows = df[df["invoice_id"] == state["invoice_id"]]

        if not rows.empty:
            state["vendor_name"]   = rows.iloc[0]["vendor_name"]
            state["invoice_total"] = float(rows["line_total"].sum())
            state["invoice_lines"] = rows.to_dict("records")
            print(f"         Vendor : {state['vendor_name']}")
            print(f"         Total  : ${state['invoice_total']:,.2f}")
        else:
            state["vendor_name"]   = "Unknown Vendor"
            state["invoice_total"] = 0.0
            state["invoice_lines"] = []
            print(f"         Invoice not found in dataset")

    except Exception as e:
        print(f"         Error loading invoice: {e}")

    return state


def node_guardrail(state: InvoiceState) -> InvoiceState:
    """
    Node 2: Guardrail check.
    Blocks high-value invoices from auto-processing.
    Key guardrail against agent tool misuse.
    """
    print(f"\n[NODE 2] Guardrail check...")
    print(f"         Invoice total : ${state['invoice_total']:,.2f}")
    print(f"         Threshold     : ${HIGH_VALUE_THRESHOLD:,.2f}")

    if state["invoice_total"] > HIGH_VALUE_THRESHOLD:
        state["guardrail_blocked"] = True
        state["final_status"] = (
            f"BLOCKED: Invoice total "
            f"${state['invoice_total']:,.2f} "
            f"exceeds threshold. Routed to manual review."
        )
        print(f"         BLOCKED - High value invoice")
    else:
        state["guardrail_blocked"] = False
        print(f"         Passed guardrail check")

    return state


def node_match(state: InvoiceState) -> InvoiceState:
    """
    Node 3: Call D2 matching model as a tool.
    Returns MATCH or MISMATCH with details.
    """
    print(f"\n[NODE 3] Running matching model...")

    result = matching_tool(state["invoice_id"])

    state["match_result"]  = result["match_result"]
    state["mismatches"]    = result["mismatches"]
    state["match_summary"] = result["summary"]

    print(f"         Result  : {result['match_result']}")
    print(f"         Details : {result['summary']}")

    return state


def node_rag_lookup(state: InvoiceState) -> InvoiceState:
    """
    Node 4: RAG knowledge base lookup.
    Retrieves contract terms, dispute history, policy notes.
    In production: queries Azure AI Search vector database.
    """
    print(f"\n[NODE 4] RAG knowledge base lookup...")
    print(f"         Vendor  : {state['vendor_name']}")

    context = rag_lookup(
        state["vendor_name"],
        state["mismatches"]
    )

    state["rag_context"] = context

    if context["contract_terms"]:
        print(f"         Contract terms found:")
        for t in context["contract_terms"]:
            print(f"           - {t}")

    if context["dispute_history"]:
        print(f"         Dispute history:")
        for h in context["dispute_history"]:
            print(f"           - {h}")

    if context["suggested_action"]:
        print(f"         Suggested: {context['suggested_action']}")

    if not context["contract_terms"] and \
       not context["dispute_history"]:
        print(f"         No prior context found for this vendor")

    return state


def node_draft_email(state: InvoiceState) -> InvoiceState:
    """
    Node 5: Draft vendor dispute email.
    Uses LLM grounded in RAG context.
    """
    print(f"\n[NODE 5] Drafting dispute email...")

    state["email_draft"] = draft_email(state)

    print(f"         Email drafted for {state['vendor_name']}")
    print("\n" + "-" * 60)
    print(state["email_draft"])
    print("-" * 60)

    return state


def node_human_approval(state: InvoiceState) -> InvoiceState:
    """
    Node 6: Human-in-the-loop approval.
    Agent pauses here. Human reviews before action.
    """
    print(f"\n[NODE 6] HUMAN APPROVAL REQUIRED")
    print(f"         Invoice : {state['invoice_id']}")
    print(f"         Vendor  : {state['vendor_name']}")
    print(f"         Issue   : {state['match_summary']}")
    print(f"\n         Review the email draft above.")
    print(f"         Type APPROVE to send or REJECT to escalate:")

    decision = input("         Your decision: ").strip().upper()

    if decision == "APPROVE":
        state["human_decision"] = "APPROVED"
        print("         Decision: Approved")
    else:
        state["human_decision"] = "REJECTED"
        print("         Decision: Rejected - escalating")

    return state


def node_execute(state: InvoiceState) -> InvoiceState:
    """
    Node 7: Execute final action.
    Sends email or escalates to AP Manager.
    """
    print(f"\n[NODE 7] Executing final action...")

    if state["human_decision"] == "APPROVED":
        state["final_status"] = (
            f"DISPUTE EMAIL SENT to {state['vendor_name']} "
            f"for invoice {state['invoice_id']}"
        )
        print(f"         Email sent to {state['vendor_name']}")
    else:
        state["final_status"] = (
            f"ESCALATED to AP Manager - "
            f"Invoice {state['invoice_id']} requires review"
        )
        print(f"         Escalated to AP Manager")

    return state


def node_auto_approve(state: InvoiceState) -> InvoiceState:
    """
    Node for clean invoices.
    Auto approves payment without human intervention.
    """
    print(f"\n[NODE] Auto-approving clean invoice...")
    state["final_status"] = (
        f"AUTO-APPROVED: Invoice {state['invoice_id']} "
        f"matches PO and GRN. Payment triggered."
    )
    print(f"       {state['final_status']}")
    return state
