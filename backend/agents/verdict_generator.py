"""
Agent 5 — VerdictGenerator
Model: llama-3.3-70b-versatile (heavy reasoning)
Job: Synthesize all evidence into a structured verdict with confidence score.
"""

import json
from core.state import PipelineState
from core.llm import get_llm

llm = get_llm("heavy")

SYSTEM_PROMPT = """You are the chief fact-checker at a world-class verification organization.

Based on the claim, supporting evidence, contradicting evidence, and source credibility data provided, 
produce a final verdict.

Verdict labels (pick the most accurate):
- "True"           — claim is well-supported by credible evidence
- "False"          — claim is directly contradicted by credible evidence
- "Misleading"     — claim contains truth but omits key context or is framed deceptively
- "Partially True" — some elements are accurate, others are not
- "Unverified"     — insufficient credible evidence found to confirm or deny

Confidence is how certain you are in this verdict (0.0–1.0), based on:
- Volume and quality of evidence
- Source credibility scores
- Degree of contradiction

Return ONLY valid JSON:
{
  "label": "True|False|Misleading|Partially True|Unverified",
  "confidence": 0.0,
  "summary": "One sentence summarizing the verdict and key reason."
}"""


async def verdict_generator(state: PipelineState) -> PipelineState:
    log = state.get("agent_log", [])
    errors = state.get("errors", [])

    claim = state.get("primary_claim", "")
    supporting = state.get("supporting_evidence", [])
    contradicting = state.get("contradicting_evidence", [])
    avg_cred = state.get("avg_source_credibility", 0.5)
    contradiction_summary = state.get("contradiction_summary", "")

    log.append("VerdictGenerator: Synthesizing evidence into verdict...")

    def fmt_evidence(items: list) -> str:
        return "\n".join([
            f"- [{e['source_domain']} | cred={e['credibility_score']:.2f}] {e['title']}: {e['snippet'][:150]}"
            for e in items[:5]
        ]) or "None found."

    prompt = f"""Claim: {claim}

Supporting Evidence ({len(supporting)} sources):
{fmt_evidence(supporting)}

Contradicting Evidence ({len(contradicting)} sources):
{fmt_evidence(contradicting)}

Contradiction Analysis: {contradiction_summary}
Average Source Credibility: {avg_cred:.2f}

Produce the verdict."""

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        verdict = json.loads(raw.strip())
        verdict["confidence"] = round(float(verdict.get("confidence", 0.5)), 2)

        log.append(f"VerdictGenerator: Verdict = {verdict['label']} (confidence {verdict['confidence']:.0%})")

    except Exception as e:
        errors.append(f"VerdictGenerator error: {str(e)}")
        verdict = {
            "label": "Unverified",
            "confidence": 0.0,
            "summary": "Verdict generation failed due to a processing error."
        }

    return {
        **state,
        "verdict": verdict,
        "agent_log": log,
        "errors": errors,
    }
