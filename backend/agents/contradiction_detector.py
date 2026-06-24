"""
Agent 4 — ContradictionDetector
Model: mixtral-8x7b-32768 (balanced reasoning)
Job: Cross-examine evidence — label each item as supporting or contradicting the claim.
     Produce a contradiction_summary if conflicts exist.
"""

import json
from core.state import PipelineState
from core.llm import get_llm

llm = get_llm("balanced")

SYSTEM_PROMPT = """You are a fact-checking analyst examining evidence for a specific claim.

For each piece of evidence provided, determine whether it:
- SUPPORTS the claim (corroborates it, confirms key facts)
- CONTRADICTS the claim (refutes it, provides conflicting facts)
- NEUTRAL (tangentially related but neither supports nor contradicts)

Then write a brief contradiction_summary explaining if there are conflicts in the evidence.

Return ONLY valid JSON:
{
  "labels": [
    {"index": 0, "stance": "supports"},
    {"index": 1, "stance": "contradicts"},
    ...
  ],
  "contradiction_summary": "Brief explanation of any conflicting evidence found, or 'No significant contradictions found.'"
}"""


async def contradiction_detector(state: PipelineState) -> PipelineState:
    log = state.get("agent_log", [])
    errors = state.get("errors", [])
    claim = state.get("primary_claim", "")
    evidence = state.get("scored_evidence", state.get("evidence", []))

    log.append("ContradictionDetector: Analyzing evidence for conflicts...")

    if not evidence:
        log.append("ContradictionDetector: No evidence to analyze.")
        return {
            **state,
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "contradiction_summary": "No evidence was found to analyze.",
            "agent_log": log,
            "errors": errors,
        }

    # Build evidence summary for the prompt (keep it concise)
    evidence_text = "\n".join([
        f"[{i}] {e['source_domain']} — {e['title']}: {e['snippet'][:200]}"
        for i, e in enumerate(evidence)
    ])

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Claim: {claim}\n\nEvidence:\n{evidence_text}"}
        ])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())

        labels = {item["index"]: item["stance"] for item in parsed.get("labels", [])}
        contradiction_summary = parsed.get("contradiction_summary", "Analysis unavailable.")

    except Exception as e:
        errors.append(f"ContradictionDetector error: {str(e)}")
        labels = {i: "supports" for i in range(len(evidence))}
        contradiction_summary = "Contradiction analysis could not be completed."

    # Tag and split evidence
    supporting = []
    contradicting = []
    for i, item in enumerate(evidence):
        stance = labels.get(i, "supports")
        tagged = {**item, "supports_claim": stance != "contradicts"}
        if stance == "contradicts":
            contradicting.append(tagged)
        else:
            supporting.append(tagged)

    log.append(f"ContradictionDetector: {len(supporting)} supporting, {len(contradicting)} contradicting sources.")

    return {
        **state,
        "supporting_evidence": supporting,
        "contradicting_evidence": contradicting,
        "contradiction_summary": contradiction_summary,
        "agent_log": log,
        "errors": errors,
    }
