"""
state.py
--------
SmartPay AP - Shared State Definition

InvoiceState is the shared memory passed between
all LangGraph nodes. Every node reads from and
writes to this state.

Why separate file:
    Every other file imports InvoiceState.
    Keeping it isolated prevents circular imports.
"""

from typing import TypedDict


class InvoiceState(TypedDict):
    # Invoice details
    invoice_id:        str
    invoice_total:     float
    vendor_name:       str
    invoice_lines:     list

    # Guardrail
    guardrail_blocked: bool

    # Matching model results
    match_result:      str
    mismatches:        list
    match_summary:     str

    # RAG context
    rag_context:       dict

    # Email
    email_draft:       str

    # Human decision
    human_decision:    str

    # Final
    final_status:      str
