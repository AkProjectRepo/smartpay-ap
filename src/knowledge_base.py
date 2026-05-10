
"""
knowledge_base.py
-----------------
SmartPay AP - Knowledge Base Data

Contains vendor contracts, dispute history,
and AP policies.

In production: this data lives in Azure AI Search
as embedded documents. This file simulates that
vector database with in-memory dictionaries.

Why separate file:
    Pure data — no logic.
    rag.py imports from here.
    Easy to swap with real database later.
"""

VENDOR_CONTRACTS = {
    "Vendor_4": {
        "ITM0048": {"agreed_price": 213.85, "currency": "USD", "contract_date": "2024-01-15"},
        "ITM0002": {"agreed_price": 359.43, "currency": "USD", "contract_date": "2024-01-15"},
        "ITM0045": {"agreed_price": 81.96,  "currency": "USD", "contract_date": "2024-01-15"},
        "ITM0049": {"agreed_price": 366.22, "currency": "USD", "contract_date": "2024-01-15"},
        "ITM0035": {"agreed_price": 443.30, "currency": "USD", "contract_date": "2024-01-15"},
    },
    "Vendor_19": {
        "ITM0011": {"agreed_price": 118.38, "currency": "EUR", "contract_date": "2024-02-01"},
        "ITM0046": {"agreed_price": 428.30, "currency": "EUR", "contract_date": "2024-02-01"},
        "ITM0007": {"agreed_price": 271.84, "currency": "EUR", "contract_date": "2024-02-01"},
    },
    "Vendor_12": {
        "ITM0016": {"agreed_price": 408.93, "currency": "GBP", "contract_date": "2024-03-10"},
        "ITM0049": {"agreed_price": 464.81, "currency": "GBP", "contract_date": "2024-03-10"},
        "ITM0033": {"agreed_price": 271.21, "currency": "GBP", "contract_date": "2024-03-10"},
    },
    "Vendor_5": {
        "ITM0006": {"agreed_price": 300.22, "currency": "INR", "contract_date": "2024-01-20"},
        "ITM0025": {"agreed_price": 398.88, "currency": "INR", "contract_date": "2024-01-20"},
    },
}

DISPUTE_HISTORY = {
    "Vendor_4": [
        {"date": "2024-03-01", "type": "PRICE_MISMATCH",    "resolution": "Credit note issued"},
        {"date": "2024-05-15", "type": "QUANTITY_MISMATCH", "resolution": "Revised invoice accepted"},
    ],
    "Vendor_19": [
        {"date": "2024-02-10", "type": "PRICE_MISMATCH",    "resolution": "Credit note issued"},
        {"date": "2024-04-20", "type": "PRICE_MISMATCH",    "resolution": "Credit note issued"},
    ],
    "Vendor_12": [
        {"date": "2024-01-05", "type": "GRN_NOT_RECEIVED",  "resolution": "Delivery confirmed after warehouse check"},
    ],
    "Vendor_5": [
        {"date": "2024-03-18", "type": "QUANTITY_MISMATCH", "resolution": "Revised invoice accepted"},
        {"date": "2024-06-02", "type": "PRICE_MISMATCH",    "resolution": "Credit note issued"},
    ],
}

AP_POLICIES = {
    "dual_approval_threshold": 45_000.00,
    "payment_terms_days":      30,
    "dispute_response_days":   5,
    "fx_tolerance_pct":        0.02,
    "price_tolerance_pct":     0.01,
    "duplicate_check_days":    90,
}
