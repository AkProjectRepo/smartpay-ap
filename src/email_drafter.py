"""
email_drafter.py
----------------
SmartPay AP - LLM Dispute Email Drafter

Drafts vendor dispute emails using LLM.
Grounded in RAG context (contract terms,
dispute history, AP policy).

Why separate file:
    Single responsibility — only email drafting.
    Easy to swap LLM provider later.
    Can be tested independently with mock state.
"""

import os
import json
from knowledge_base import AP_POLICIES


def draft_email(state: dict) -> str:
    """
    Drafts a professional vendor dispute email.

    Uses GPT-4 if OPENAI_API_KEY is set.
    Falls back to mock email if no key available.

    Args:
        state: InvoiceState dict containing:
               vendor_name, invoice_id,
               mismatches, rag_context

    Returns:
        Email string ready for human review
    """

    vendor     = state["vendor_name"]
    inv_id     = state["invoice_id"]
    mismatches = state["mismatches"]
    rag        = state.get("rag_context", {})

    # Build RAG context string
    rag_context_str = _build_rag_context_string(rag)

    # Try real LLM first
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and api_key != "sk-your-key-here":
        email = _draft_with_llm(
            vendor, inv_id, mismatches, rag_context_str
        )
        if email:
            return email

    # Fall back to mock email
    return _draft_mock_email(vendor, inv_id, mismatches, rag)


def _build_rag_context_string(rag: dict) -> str:
    """Converts RAG context dict to formatted string for LLM prompt."""
    parts = []

    if rag.get("contract_terms"):
        parts.append("Contract Terms:\n" + "\n".join(
            f"  - {t}" for t in rag["contract_terms"]
        ))

    if rag.get("dispute_history"):
        parts.append("Past Dispute History:\n" + "\n".join(
            f"  - {h}" for h in rag["dispute_history"]
        ))

    if rag.get("suggested_action"):
        parts.append(
            f"Suggested Resolution: {rag['suggested_action']}"
        )

    return "\n\n".join(parts)


def _draft_with_llm(
    vendor: str,
    inv_id: str,
    mismatches: list,
    rag_context_str: str
) -> str:
    """Calls GPT-4 to draft dispute email."""
    try:
        from langchain_openai import ChatOpenAI
        from langchain.schema import HumanMessage

        prompt = f"""
You are an AP specialist at Acme Manufacturing.
Write a professional vendor dispute email.

Vendor: {vendor}
Invoice: {inv_id}
Discrepancies: {json.dumps(mismatches, indent=2)}

Context from knowledge base:
{rag_context_str}

Requirements:
- Professional but firm tone
- Reference contract terms where available
- Reference suggested resolution approach
- Request correction within 
  {AP_POLICIES['dispute_response_days']} business days
- Sign off as Acme Manufacturing AP Team
- Under 200 words
"""
        llm      = ChatOpenAI(model="gpt-4", temperature=0.3)
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content

    except Exception as e:
        print(f"         LLM error: {e}. Using mock email.")
        return ""


def _draft_mock_email(
    vendor: str,
    inv_id: str,
    mismatches: list,
    rag: dict
) -> str:
    """Generates mock dispute email using RAG context."""

    mismatch_lines = "\n".join([
        f"  - Line {m['line']} ({m['item']}): {m['detail']}"
        for m in mismatches
    ])

    contract_section = ""
    if rag.get("contract_terms"):
        contract_section = "\nContract Reference:\n" + "\n".join(
            f"  - {t}" for t in rag["contract_terms"]
        )

    resolution_section = ""
    if rag.get("suggested_action"):
        resolution_section = (
            f"\nBased on previous dispute resolutions, "
            f"we request: {rag['suggested_action']}."
        )

    return f"""Subject: Invoice Dispute - {inv_id}

Dear {vendor} Finance Team,

We are writing regarding Invoice {inv_id}.

Upon reconciliation against our PO and GRN records,
we found the following discrepancies:

{mismatch_lines}
{contract_section}

Please provide a revised invoice or written
clarification within
{AP_POLICIES['dispute_response_days']} business days.
{resolution_section}

Best regards,
Acme Manufacturing - Accounts Payable Team
ap-disputes@acme-manufacturing.com"""
