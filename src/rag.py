"""
rag.py
------
SmartPay AP - RAG Lookup

Retrieves relevant context from knowledge base
before dispute email is drafted.

In production: queries Azure AI Search vector database
using semantic similarity search over embedded documents.

Why separate file:
    Single responsibility — only RAG logic here.
    Imports from knowledge_base.py.
    nodes.py imports from here.
"""

from knowledge_base import (
    VENDOR_CONTRACTS,
    DISPUTE_HISTORY,
    AP_POLICIES,
)


def rag_lookup(vendor_name: str, mismatches: list) -> dict:
    """
    Retrieves relevant context for dispute email drafting.

    Three lookups:
    1. Vendor contract terms — agreed prices for mismatched items
    2. Dispute history      — past resolutions with this vendor
    3. AP policy notes      — internal rules that apply

    Args:
        vendor_name: e.g. "Vendor_19"
        mismatches:  list of mismatch dicts from matching_tool

    Returns:
        dict with contract_terms, dispute_history,
        policy_notes, suggested_action
    """
    results = {
        "contract_terms":   [],
        "dispute_history":  [],
        "policy_notes":     [],
        "suggested_action": ""
    }

    # 1. Contract lookup
    contracts = VENDOR_CONTRACTS.get(vendor_name, {})
    for m in mismatches:
        item = m.get("item", "")
        if item in contracts:
            c = contracts[item]
            results["contract_terms"].append(
                f"Item {item}: agreed price "
                f"{c['currency']} {c['agreed_price']} "
                f"per contract dated {c['contract_date']}"
            )

    # 2. Dispute history
    history = DISPUTE_HISTORY.get(vendor_name, [])
    if history:
        for h in history[-2:]:
            results["dispute_history"].append(
                f"{h['date']}: {h['type']} "
                f"resolved via {h['resolution']}"
            )

        # Detect resolution pattern
        resolutions = [h["resolution"] for h in history]
        credit_count = sum(
            1 for r in resolutions if "Credit note" in r
        )
        if credit_count >= 2:
            results["suggested_action"] = (
                f"Request credit note — vendor has resolved "
                f"{credit_count} disputes this way previously"
            )
        elif any("Revised invoice" in r for r in resolutions):
            results["suggested_action"] = (
                "Request revised invoice — vendor has accepted "
                "this resolution approach previously"
            )

    # 3. Policy notes
    results["policy_notes"].append(
        f"Dispute response required within "
        f"{AP_POLICIES['dispute_response_days']} business days"
    )
    results["policy_notes"].append(
        f"Price tolerance: "
        f"{AP_POLICIES['price_tolerance_pct'] * 100}% — "
        f"deviations above this must be disputed"
    )

    return results
