
import os
import json
import pandas as pd
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
LABELED_FILE = os.path.join(DATA_DIR, "labeled_dataset.csv")

# Constants
HIGH_VALUE_THRESHOLD = 50_000.00


# STATE
class InvoiceState(TypedDict):
    invoice_id:        str
    invoice_total:     float
    vendor_name:       str
    invoice_lines:     list
    guardrail_blocked: bool
    match_result:      str
    mismatches:        list
    match_summary:     str
    email_draft:       str
    human_decision:    str
    final_status:      str


# TOOL — D2 Matching Model
def matching_tool(invoice_id: str) -> dict:
    if not invoice_id or not isinstance(invoice_id, str):
        return {
            "match_result": "ERROR",
            "mismatches": [],
            "summary": "Invalid invoice_id"
        }

    try:
        df = pd.read_csv(LABELED_FILE)
    except FileNotFoundError:
        return {
            "match_result": "ERROR",
            "mismatches": [],
            "summary": "Dataset not found. Run D2 notebook first."
        }

    lookup_id = invoice_id.replace("_DUP", "")
    rows = df[df["invoice_id"] == lookup_id]

    if rows.empty:
        return {
            "match_result": "NOT_FOUND",
            "mismatches": [],
            "summary": f"Invoice {invoice_id} not found."
        }

    mismatches = []

    for _, row in rows.iterrows():
        if row["quantity"] != row["po_quantity"]:
            mismatches.append({
                "line": int(row["line_item_number"]),
                "item": row["item_code"],
                "type": "QUANTITY_MISMATCH",
                "detail": f"Invoice qty={row['quantity']}, "
                          f"PO qty={row['po_quantity']}"
            })

        price_diff_pct = abs(
            row["unit_price"] - row["po_unit_price"]
        ) / (row["po_unit_price"] + 1e-9)

        if price_diff_pct > 0.01:
            mismatches.append({
                "line": int(row["line_item_number"]),
                "item": row["item_code"],
                "type": "PRICE_MISMATCH",
                "detail": f"Invoice price={row['unit_price']}, "
                          f"PO price={row['po_unit_price']}"
            })

        if row["grn_quantity"] == 0:
            mismatches.append({
                "line": int(row["line_item_number"]),
                "item": row["item_code"],
                "type": "GRN_NOT_RECEIVED",
                "detail": "Goods not received yet."
            })

    match_result = "MISMATCH" if mismatches else "MATCH"

    if match_result == "MATCH":
        summary = f"Invoice {invoice_id}: All lines match PO and GRN."
    else:
        lines = [
            f"  Line {m['line']} ({m['item']}): "
            f"{m['type']} — {m['detail']}"
            for m in mismatches
        ]
        summary = (
            f"Invoice {invoice_id}: "
            f"{len(mismatches)} mismatch(es) found.\n"
            + "\n".join(lines)
        )

    return {
        "match_result": match_result,
        "mismatches": mismatches,
        "summary": summary
    }


# LLM — Dispute Email Drafter
def draft_email(state: InvoiceState) -> str:
    vendor = state["vendor_name"]
    inv_id = state["invoice_id"]
    mismatches = state["mismatches"]

    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key != "sk-your-key-here":
        try:
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage

            prompt = f"""
You are an AP specialist at Acme Manufacturing.
Write a professional vendor dispute email.

Vendor: {vendor}
Invoice: {inv_id}
Issues: {json.dumps(mismatches, indent=2)}

Requirements:
- Professional but firm tone
- Reference invoice ID and line items
- Request correction within 5 business days
- Sign off as Acme Manufacturing AP Team
- Under 150 words
"""
            llm = ChatOpenAI(model="gpt-4", temperature=0.3)
            response = llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            print(f"LLM error: {e}. Using mock email.")

    mismatch_lines = "\n".join([
        f"  - Line {m['line']} ({m['item']}): {m['detail']}"
        for m in mismatches
    ])

    return f"""Subject: Invoice Dispute - {inv_id}

Dear {vendor} Finance Team,

We are writing regarding Invoice {inv_id}.

Upon reconciliation against our PO and GRN records,
we found the following discrepancies:

{mismatch_lines}

Please provide a revised invoice or written clarification
within 5 business days.

Best regards,
Acme Manufacturing - Accounts Payable Team
ap-disputes@acme-manufacturing.com"""


# NODES

def node_load_invoice(state: InvoiceState) -> InvoiceState:
    print(f"\n[NODE 1] Loading invoice {state['invoice_id']}...")

    try:
        df = pd.read_csv(LABELED_FILE)
        rows = df[df["invoice_id"] == state["invoice_id"]]

        if not rows.empty:
            state["vendor_name"] = rows.iloc[0]["vendor_name"]
            state["invoice_total"] = float(rows["line_total"].sum())
            state["invoice_lines"] = rows.to_dict("records")
            print(f"         Vendor : {state['vendor_name']}")
            print(f"         Total  : ${state['invoice_total']:,.2f}")
        else:
            state["vendor_name"] = "Unknown Vendor"
            state["invoice_total"] = 0.0
            state["invoice_lines"] = []
            print(f"         Invoice not found in dataset")
    except Exception as e:
        print(f"         Error: {e}")

    return state


def node_guardrail(state: InvoiceState) -> InvoiceState:
    print(f"\n[NODE 2] Guardrail check...")
    print(f"         Invoice total : ${state['invoice_total']:,.2f}")
    print(f"         Threshold     : ${HIGH_VALUE_THRESHOLD:,.2f}")

    if state["invoice_total"] > HIGH_VALUE_THRESHOLD:
        state["guardrail_blocked"] = True
        state["final_status"] = (
            f"BLOCKED: Invoice total ${state['invoice_total']:,.2f} "
            f"exceeds threshold. Routed to manual review."
        )
        print(f"         BLOCKED - High value invoice")
    else:
        state["guardrail_blocked"] = False
        print(f"         Passed guardrail check")

    return state


def node_match(state: InvoiceState) -> InvoiceState:
    print(f"\n[NODE 3] Running matching model...")

    result = matching_tool(state["invoice_id"])

    state["match_result"] = result["match_result"]
    state["mismatches"] = result["mismatches"]
    state["match_summary"] = result["summary"]

    print(f"         Result  : {result['match_result']}")
    print(f"         Details : {result['summary']}")

    return state


def node_draft_email(state: InvoiceState) -> InvoiceState:
    print(f"\n[NODE 4] Drafting dispute email...")

    state["email_draft"] = draft_email(state)

    print(f"         Email drafted for {state['vendor_name']}")
    print("\n" + "-" * 50)
    print(state["email_draft"])
    print("-" * 50)

    return state


def node_human_approval(state: InvoiceState) -> InvoiceState:
    print(f"\n[NODE 5] HUMAN APPROVAL REQUIRED")
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
    print(f"\n[NODE 6] Executing final action...")

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
    print(f"\n[NODE] Auto-approving clean invoice...")
    state["final_status"] = (
        f"AUTO-APPROVED: Invoice {state['invoice_id']} "
        f"matches PO and GRN. Payment triggered."
    )
    print(f"       {state['final_status']}")
    return state


# BUILD LANGGRAPH

def build_graph():
    try:
        from langgraph.graph import StateGraph, END

        graph = StateGraph(InvoiceState)

        graph.add_node("load_invoice", node_load_invoice)
        graph.add_node("guardrail", node_guardrail)
        graph.add_node("match", node_match)
        graph.add_node("draft_email", node_draft_email)
        graph.add_node("human_approval", node_human_approval)
        graph.add_node("execute", node_execute)
        graph.add_node("auto_approve", node_auto_approve)

        graph.set_entry_point("load_invoice")
        graph.add_edge("load_invoice", "guardrail")

        graph.add_conditional_edges(
            "guardrail",
            lambda s: "blocked" if s["guardrail_blocked"] else "continue",
            {"blocked": END, "continue": "match"}
        )

        graph.add_conditional_edges(
            "match",
            lambda s: "mismatch" if s["match_result"] == "MISMATCH"
                      else "clean",
            {"mismatch": "draft_email", "clean": "auto_approve"}
        )

        graph.add_edge("draft_email", "human_approval")
        graph.add_edge("human_approval", "execute")
        graph.add_edge("execute", END)
        graph.add_edge("auto_approve", END)

        return graph.compile()

    except ImportError:
        print("LangGraph not available. Using manual workflow.")
        return None


# RUN AGENT

def run_agent(invoice_id: str):
    print("=" * 60)
    print("  SmartPay AP - Agentic Reconciliation Workflow (D3)")
    print("=" * 60)
    print(f"  Processing Invoice: {invoice_id}")
    print("=" * 60)

    initial_state: InvoiceState = {
        "invoice_id":        invoice_id,
        "invoice_total":     0.0,
        "vendor_name":       "",
        "invoice_lines":     [],
        "guardrail_blocked": False,
        "match_result":      "",
        "mismatches":        [],
        "match_summary":     "",
        "email_draft":       "",
        "human_decision":    "",
        "final_status":      "",
    }

    graph = build_graph()

    if graph:
        print("\n[INFO] Running with LangGraph\n")
        final_state = graph.invoke(initial_state)
    else:
        print("\n[INFO] Running manual workflow\n")
        state = initial_state
        state = node_load_invoice(state)
        state = node_guardrail(state)

        if not state["guardrail_blocked"]:
            state = node_match(state)

            if state["match_result"] == "MISMATCH":
                state = node_draft_email(state)
                state = node_human_approval(state)
                state = node_execute(state)
            else:
                state = node_auto_approve(state)

        final_state = state

    print("\n" + "=" * 60)
    print("  FINAL STATUS")
    print("=" * 60)
    print(f"  {final_state['final_status']}")
    print("=" * 60)

    return final_state


# MAIN

if __name__ == "__main__":
    try:
        df = pd.read_csv(LABELED_FILE)
        mismatch_invoice = df[df["is_mismatch"] == 1]["invoice_id"].iloc[0]
        print(f"\nDemo invoice: {mismatch_invoice}")
        run_agent(mismatch_invoice)

    except FileNotFoundError:
        print("labeled_dataset.csv not found.")
        print("Run D2 notebook first to generate the dataset.")
