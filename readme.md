# SmartPay AP — Agentic AI Platform for Invoice Reconciliation

AI Architect Case Study | HTC Global Services | May 2026

**Author:** Akhil Ahmed
**GitHub:** https://github.com/AkProjectRepo/smartpay-ap

-----

## What This Is

SmartPay AP automates Accounts Payable invoice reconciliation for Acme Manufacturing.

Acme processes 1 million invoices/month across 25 countries and 1,000+ suppliers.
Manual reconciliation takes 3–5 days per cycle and has a 2–3% error rate.

This solution detects mismatches automatically, drafts vendor dispute emails grounded
in contract data (RAG), and routes flagged invoices for human approval before any
payment action is taken.

-----

## Deliverables

|ID|What                         |Location                               |
|--|-----------------------------|---------------------------------------|
|D1|Architecture Deck (13 slides)|docs/SmartPay_AP_Architecture_D1.pptx  |
|D2|Matching Model Notebook      |notebooks/D2_matching_model.ipynb      |
|D3|Agentic Workflow             |src/                                   |
|D4|Responsible AI Brief         |docs/SmartPay_AP_Responsible_AI_D4.pptx|
|D6|This README                  |README.md                              |

-----

## Project Structure

```
smartpay-ap/
├── src/
│   ├── state.py            # Shared InvoiceState TypedDict
│   ├── knowledge_base.py   # Vendor contracts, dispute history, AP policies
│   ├── rag.py              # RAG lookup logic
│   ├── matching_tool.py    # D2 matching model as agent tool
│   ├── email_drafter.py    # LLM dispute email drafting
│   ├── nodes.py            # All 7 LangGraph node functions
│   ├── graph.py            # LangGraph graph builder
│   └── agent_workflow.py   # Main agent runner
├── data/
│   ├── invoices.csv        # AcmeMini dataset (300 invoices)
│   ├── purchase_orders.csv # Generated synthetic PO data
│   ├── grn.csv             # Generated synthetic GRN data
│   └── labeled_dataset.csv # Merged dataset with injected mismatches
├── notebooks/
│   └── D2_matching_model.ipynb
├── docs/
│   ├── SmartPay_AP_Architecture_D1.pptx
│   └── SmartPay_AP_Responsible_AI_D4.pptx    
├── run.py                  # Simple runner script
├── .env.example            # Environment variable template
└── requirements.txt
```

-----

## Setup Instructions

### Prerequisites

- Python 3.11
- Git
- OpenAI API key (optional — mock email used if not set)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/AkProjectRepo/smartpay-ap.git
cd smartpay-ap
```

### Step 2 — Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set Up Environment Variables

```bash
cp .env.example .env
```

Add your OpenAI API key to .env:

```
OPENAI_API_KEY=sk-your-key-here
```

If no key is set, agent uses mock email. Everything else works without it.

-----

## How to Run

### Run D2 — Matching Model Notebook

```bash
jupyter notebook
```

Open notebooks/D2_matching_model.ipynb and run all cells.

### Run D3 — Agent Workflow

```bash
python run.py              # auto-selects first mismatch invoice
python run.py INV0002      # price mismatch — full RAG + email flow
python run.py INV0001      # clean invoice — auto-approved
python run.py INV0003      # quantity + GRN mismatch
```

Type APPROVE or REJECT when agent pauses for human approval.

### Run UI Demo

Open smartpay_demo.html in any browser — no server needed.
Click any invoice to see the full agent workflow visually.

-----

## Agent Workflow (D3)

7-node LangGraph workflow:

```
Invoice arrives
      |
NODE 1: Load Invoice       — fetch vendor, total, line items
      |
NODE 2: Guardrail Check    — block invoices > $50,000
      |
NODE 3: Matching Model     — D2 model checks invoice vs PO vs GRN
      |
   MATCH ——————————> Auto-Approve (payment triggered)
      |
  MISMATCH
      |
NODE 4: RAG Lookup         — retrieve contract terms + dispute history
      |
NODE 5: Draft Email        — LLM generates dispute email
      |
NODE 6: Human Approval     — HITL pause — human reviews
      |
NODE 7: Execute            — send email or escalate to manager
```

-----

## Matching Model (D2)

Two-layer design:

Layer 1 — Rule-Based Engine:

- Quantity mismatch (invoice qty != PO qty)
- Price mismatch (deviation > 1% from agreed PO price)
- GRN not received (goods receipt qty = 0)
- Duplicate invoice submission
- Item not in PO
- Currency mismatch

Layer 2 — Random Forest (scikit-learn):

- 13 engineered features (qty delta %, price delta %, GRN gap)
- 100 estimators, balanced class weights
- Trained on 1,200 labeled examples (80/20 split)

Evaluation Results:

- Accuracy: 89%
- Precision (MISMATCH): 100%
- Recall (MISMATCH): 57%
- False Positive Rate: 0%

-----

## RAG Implementation

Retrieves context before drafting dispute emails:

1. Vendor Contract Lookup — agreed prices for mismatched items
1. Dispute History — past resolutions with this vendor
1. AP Policy — internal rules and response timeframes

Production: Azure AI Search vector database with embeddings.
MVP: in-memory dictionaries in src/knowledge_base.py.

-----

## MCP Integration (Production)

Uses MCP (Model Context Protocol) for standardised connectivity.

|MCP Server           |Connects To    |Purpose                               |
|---------------------|---------------|--------------------------------------|
|SAP MCP Server       |SAP BAPI/RFC   |PO lookup, GRN lookup, payment trigger|
|Oracle MCP Server    |Oracle REST API|PO and GRN lookup                     |
|Azure Blob MCP Server|Azure Storage  |Invoice document retrieval            |
|Graph API MCP Server |Microsoft 365  |Email monitoring and sending          |

Adding a new data source = deploy new MCP server, no agent code changes.

-----

## Access Control

Azure AD with RBAC — four roles:

|Role              |Permissions                   |
|------------------|------------------------------|
|AP Clerk          |View invoices and results only|
|AP Specialist     |Approve/reject up to $10K     |
|AP Manager        |Approve/reject up to $50K     |
|Finance Controller|Approve any amount            |

All roles enforced at Azure API Management before reaching the agent.
The $50K guardrail is hardcoded — cannot be overridden by any role.

-----

## Audit Trail

Every agent decision logged with:

- Timestamp, Invoice ID, Node name
- User ID and role (human decisions)
- Decision and rationale
- Model confidence score

Real-time: Azure Monitor (searchable, alertable)
Immutable: AWS S3 (tamper-proof, 7-year retention)
Reports: Power BI dashboard

-----

## Assumptions

1. Dataset is synthetic — generated from AcmeMini invoices.csv
1. PO and GRN data generated synthetically (SAP/Oracle not connected)
1. 25% mismatch rate injected for model training
1. Vendor contracts simulated in knowledge_base.py
1. Email sending simulated (printed to console)
1. SAP/Oracle payment triggers simulated
1. Azure Event Hubs replaced by direct CSV load in MVP
1. MCP servers simulated by direct Python function calls in MVP
1. Currency conversion not implemented (Phase 2)
1. Multi-tenant support not implemented (Phase 2)

-----

## Design Decisions

LangGraph over CrewAI:
AP reconciliation is a fixed sequential workflow. LangGraph gives
deterministic control flow and native HITL. CrewAI suits autonomous
multi-agent tasks — not this use case.

Rules + Random Forest over Neural Networks:
Rules are explainable — auditors need clear reasons for every flag.
RF catches subtle patterns. Neural nets are black-box and overkill
for tabular AP data.

RAG over Fine-tuning:
Vendor contracts change frequently. RAG retrieves latest data without
retraining. Fine-tuning becomes stale after every contract update.

MCP over Custom Connectors:
MCP gives standardised connectivity. Adding a new system means
deploying a new MCP server — no agent code changes needed.

100% Precision over Recall:
False positives (blocking good invoices) damage supplier relationships.
False negatives are caught in finance audit. 57% recall is intentional.

Azure Event Hubs over Apache Kafka:
Event Hubs is Kafka-compatible but fully managed by Microsoft.
Existing Kafka producers connect without code changes.

-----

## Tech Stack

### Built and Tested (MVP)

|Component           |Technology  |Version|
|--------------------|------------|-------|
|Language            |Python      |3.11   |
|Data manipulation   |pandas      |2.2.2  |
|Numerical operations|numpy       |1.26.4 |
|ML model            |scikit-learn|1.5.0  |
|Visualisation       |matplotlib  |3.10.9 |
|Agent framework     |LangGraph   |0.1.5  |
|LLM abstraction     |LangChain   |0.2.5  |
|LLM API             |OpenAI GPT-4|1.30.5 |
|Notebook            |Jupyter     |1.0.0  |

### Production Architecture

|Component           |Technology                         |
|--------------------|-----------------------------------|
|Document extraction |Azure Form Recognizer              |
|Event streaming     |Azure Event Hubs (Kafka-compatible)|
|API gateway         |Azure API Management               |
|Identity and access |Azure Active Directory + RBAC      |
|Agent hosting       |Azure Container Apps               |
|Secrets management  |Azure Key Vault                    |
|Audit log storage   |AWS S3 (immutable)                 |
|ML training at scale|Amazon SageMaker                   |
|Tool connectivity   |MCP (Model Context Protocol)       |
|Model registry      |MLflow                             |
|Monitoring          |Azure Monitor + Power BI           |

-----

## Open Source Credits

- LangGraph — MIT License — https://github.com/langchain-ai/langgraph
- scikit-learn — BSD License — https://github.com/scikit-learn/scikit-learn
- LangChain — MIT License — https://github.com/langchain-ai/langchain
- pandas — BSD License — https://github.com/pandas-dev/pandas
- matplotlib — PSF License — https://github.com/matplotlib/matplotlib

-----

## Author

Akhil Ahmed
AI Architect — Case Study Submission
HTC Global Services — May 2026
GitHub: https://github.com/AkProjectRepo/smartpay-ap