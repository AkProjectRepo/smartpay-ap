# SmartPay AP — Agentic AI Platform for Invoice Reconciliation

AI Architect Case Study | HTC Global Services | May 2026

---

## What This Is

SmartPay AP automates Accounts Payable invoice reconciliation for Acme Manufacturing.

Acme processes 1 million invoices/month across 25 countries and 1,000+ suppliers.
Manual reconciliation takes 3–5 days per cycle and has a 2–3% error rate.

This solution detects mismatches automatically, drafts vendor dispute emails,
and routes flagged invoices for human approval before any payment action is taken.

---

## Deliverables

| ID | What | Location |
|----|------|----------|
| D1 | Architecture Deck (12 slides) | docs/SmartPay_AP_Architecture_D1.pptx |
| D2 | Matching Model Notebook | notebooks/D2_matching_model.ipynb |
| D3 | Agentic Workflow | src/ |
| D4 | Responsible AI Brief | docs/SmartPay_AP_Responsible_AI_D4.pptx |
| D6 | This README | README.md |

---

## Project Structure

smartpay-ap/
├── src/
│   ├── state.py
│   ├── knowledge_base.py
│   ├── rag.py
│   ├── matching_tool.py
│   ├── email_drafter.py
│   ├── nodes.py
│   ├── graph.py
│   └── agent_workflow.py
├── data/
│   ├── invoices.csv
│   ├── purchase_orders.csv
│   ├── grn.csv
│   └── labeled_dataset.csv
├── notebooks/
│   └── D2_matching_model.ipynb
├── docs/
├── .env.example
├── requirements.txt
└── run.py

---

## Setup Instructions

### Prerequisites
- Python 3.11
- Git
- OpenAI API key (optional)

### Step 1 — Clone the Repository
git clone https://github.com/AkProjectRepo/smartpay-ap.git
cd smartpay-ap

### Step 2 — Create Virtual Environment
python3.11 -m venv venv
source venv/bin/activate

### Step 3 — Install Dependencies
pip install -r requirements.txt

### Step 4 — Set Up Environment Variables
cp .env.example .env
Add your OpenAI API key to .env:
OPENAI_API_KEY=sk-your-key-here

---

## How to Run

### Run D2 — Matching Model Notebook
jupyter notebook
Open notebooks/D2_matching_model.ipynb and run all cells.

### Run D3 — Agent Workflow
python run.py              # auto-selects mismatch invoice
python run.py INV0002      # specific mismatch invoice
python run.py INV0001      # clean invoice (auto-approved)

When agent pauses type APPROVE or REJECT.

---

## Agent Workflow (D3)

7 nodes:
1. Load Invoice
2. Guardrail Check (block > $50K)
3. Matching Model (D2 as tool)
4. RAG Lookup (contracts, history, policy)
5. Draft Email (LLM)
6. Human Approval (HITL)
7. Execute (send or escalate)

---

## Matching Model (D2)

Layer 1 — Rules: quantity, price, GRN, duplicate checks
Layer 2 — Random Forest: 13 features, 100 estimators

Results:
- Accuracy: 89%
- Precision: 100%
- Recall: 57%
- False Positive Rate: 0%

---

## Assumptions

1. Dataset is synthetic — generated from AcmeMini invoices.csv
2. PO and GRN data generated synthetically
3. 25% mismatch rate injected for model training
4. Vendor contracts simulated in knowledge_base.py
5. Email sending simulated (print to console)
6. SAP/Oracle payment triggers simulated
7. Currency conversion not implemented (Phase 2)
8. Multi-tenant support not implemented (Phase 2)

---

## Design Decisions

LangGraph over CrewAI: Fixed sequential workflow needs
deterministic control flow and native HITL support.

Rules + Random Forest over pure ML: Rules are explainable
for auditors. ML catches subtle patterns rules miss.

RAG over Fine-tuning: Vendor contracts change frequently.
RAG retrieves latest data without retraining.

100% Precision over Recall: False positives damage supplier
relationships. False negatives caught in finance audit.

---

## Tech Stack

Agent framework: LangGraph
ML model: scikit-learn Random Forest
LLM: OpenAI GPT-4 / mock
Data: pandas, numpy
Notebook: Jupyter
Document extraction (prod): Azure Form Recognizer
Vector database (prod): Azure AI Search
ERP integration (prod): SAP BAPI, Oracle REST API
MLOps (prod): MLflow
Event streaming (prod): Apache Kafka

---

## Open Source Credits

LangGraph — MIT License — https://github.com/langchain-ai/langgraph
scikit-learn — BSD License — https://github.com/scikit-learn/scikit-learn
LangChain — MIT License — https://github.com/langchain-ai/langchain
pandas — BSD License — https://github.com/pandas-dev/pandas

---

## Author

Akhil Ahmed
AI Architect — Case Study Submission
HTC Global Services — May 2026
GitHub: https://github.com/AkProjectRepo/smartpay-ap
