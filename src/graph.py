"""
graph.py
--------
SmartPay AP - LangGraph Graph Builder

Builds and compiles the LangGraph workflow.
Defines all nodes, edges and conditional routing.

Why separate file:
    Single responsibility — only graph structure.
    Imports from nodes.py and state.py.
    agent_workflow.py imports from here.

Graph structure:
    load_invoice
        -> guardrail
            -> [blocked]  END
            -> [continue] match
                -> [clean]    auto_approve -> END
                -> [mismatch] rag_lookup
                    -> draft_email
                        -> human_approval
                            -> execute -> END
"""

from state import InvoiceState
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


def build_graph():
    """
    Builds and compiles the LangGraph workflow.
    Returns compiled graph or None if LangGraph
    is not installed.
    """
    try:
        from langgraph.graph import StateGraph, END

        graph = StateGraph(InvoiceState)

        # Add all nodes
        graph.add_node("load_invoice",   node_load_invoice)
        graph.add_node("guardrail",      node_guardrail)
        graph.add_node("match",          node_match)
        graph.add_node("rag_lookup",     node_rag_lookup)
        graph.add_node("draft_email",    node_draft_email)
        graph.add_node("human_approval", node_human_approval)
        graph.add_node("execute",        node_execute)
        graph.add_node("auto_approve",   node_auto_approve)

        # Entry point
        graph.set_entry_point("load_invoice")

        # Fixed edges
        graph.add_edge("load_invoice", "guardrail")

        # Conditional: guardrail result
        graph.add_conditional_edges(
            "guardrail",
            lambda s: "blocked" if s["guardrail_blocked"]
                      else "continue",
            {
                "blocked":  END,
                "continue": "match"
            }
        )

        # Conditional: match result
        graph.add_conditional_edges(
            "match",
            lambda s: "mismatch" if s["match_result"] == "MISMATCH"
                      else "clean",
            {
                "mismatch": "rag_lookup",
                "clean":    "auto_approve"
            }
        )

        # Fixed edges — mismatch path
        graph.add_edge("rag_lookup",     "draft_email")
        graph.add_edge("draft_email",    "human_approval")
        graph.add_edge("human_approval", "execute")
        graph.add_edge("execute",        END)

        # Fixed edges — clean path
        graph.add_edge("auto_approve", END)

        return graph.compile()

    except ImportError:
        print("LangGraph not available. Using manual workflow.")
        return None
