"""
TruthLens AI — LangGraph Pipeline

DAG flow:
  ClaimExtractor → EvidenceHunter → CredibilityScorer
                                          ↓
                              ContradictionDetector
                                          ↓
                               VerdictGenerator
                                          ↓
                               ExplanationWriter
"""

from langgraph.graph import StateGraph, END
from core.state import PipelineState
from agents.claim_extractor import claim_extractor
from agents.evidence_hunter import evidence_hunter
from agents.credibility_scorer import credibility_scorer
from agents.contradiction_detector import contradiction_detector
from agents.verdict_generator import verdict_generator
from agents.explanation_writer import explanation_writer


def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    # Register nodes
    graph.add_node("claim_extractor", claim_extractor)
    graph.add_node("evidence_hunter", evidence_hunter)
    graph.add_node("credibility_scorer", credibility_scorer)
    graph.add_node("contradiction_detector", contradiction_detector)
    graph.add_node("verdict_generator", verdict_generator)
    graph.add_node("explanation_writer", explanation_writer)

    # Define the linear DAG
    graph.set_entry_point("claim_extractor")
    graph.add_edge("claim_extractor", "evidence_hunter")
    graph.add_edge("evidence_hunter", "credibility_scorer")
    graph.add_edge("credibility_scorer", "contradiction_detector")
    graph.add_edge("contradiction_detector", "verdict_generator")
    graph.add_edge("verdict_generator", "explanation_writer")
    graph.add_edge("explanation_writer", END)

    return graph.compile()


# Singleton — compile once, reuse per request
pipeline = build_pipeline()


async def run_pipeline(claim_text: str) -> PipelineState:
    """
    Run the full TruthLens pipeline on a user-submitted claim.
    Returns the final PipelineState with all agent outputs.
    """
    initial_state: PipelineState = {
        "raw_input": claim_text,
        "claims": [],
        "primary_claim": "",
        "evidence": [],
        "scored_evidence": [],
        "avg_source_credibility": 0.0,
        "supporting_evidence": [],
        "contradicting_evidence": [],
        "contradiction_summary": "",
        "verdict": {},
        "explanation": "",
        "errors": [],
        "agent_log": [],
    }

    result = await pipeline.ainvoke(initial_state)
    return result
