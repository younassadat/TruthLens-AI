"""
TruthLens AI — Shared pipeline state.
Every agent reads from and writes to this TypedDict.
LangGraph passes it through the DAG automatically.
"""

from typing import TypedDict, Optional
from pydantic import BaseModel


class EvidenceItem(BaseModel):
    title: str
    url: str
    snippet: str
    source_domain: str
    credibility_score: float = 0.0  # filled by CredibilityScorer
    supports_claim: bool = True      # filled by ContradictionDetector


class Verdict(BaseModel):
    label: str          # "True" | "False" | "Misleading" | "Unverified" | "Partially True"
    confidence: float   # 0.0 – 1.0
    summary: str        # one-sentence summary


class PipelineState(TypedDict):
    # ── Input ──
    raw_input: str                        # original user submission

    # ── Agent 1: ClaimExtractor ──
    claims: list[str]                     # extracted verifiable claims
    primary_claim: str                    # the single most verifiable claim

    # ── Agent 2: EvidenceHunter ──
    evidence: list[dict]                  # list of EvidenceItem dicts

    # ── Agent 3: CredibilityScorer ──
    scored_evidence: list[dict]           # evidence with credibility_score filled in
    avg_source_credibility: float

    # ── Agent 4: ContradictionDetector ──
    supporting_evidence: list[dict]
    contradicting_evidence: list[dict]
    contradiction_summary: str

    # ── Agent 5: VerdictGenerator ──
    verdict: dict                         # Verdict dict

    # ── Agent 6: ExplanationWriter ──
    explanation: str                      # plain-language explanation for the user

    # ── Metadata ──
    errors: list[str]
    agent_log: list[str]                  # trace of which agents ran and what they found
