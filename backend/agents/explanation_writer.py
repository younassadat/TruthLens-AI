"""
Agent 6 — ExplanationWriter
Model: llama-3.3-70b-versatile (heavy — quality prose matters here)
Job: Write a clear, plain-language explanation of the verdict for non-expert users.
     This is the "why" — the most user-facing output of the entire pipeline.
"""

from core.state import PipelineState
from core.llm import get_llm

llm = get_llm("heavy")

SYSTEM_PROMPT = """You are a science communicator and fact-checker writing for a general audience.

Write a clear, plain-language explanation of how TruthLens AI reached its verdict on a claim.

Your explanation should:
1. Restate the claim simply
2. Explain what the investigation found (key supporting and contradicting evidence)
3. Explain WHY the verdict was reached (not just what it is)
4. Note any important caveats or missing context
5. Be 3–5 short paragraphs, written in plain English — no jargon
6. Be honest about uncertainty when confidence is low
7. NOT tell people what to believe — present the evidence and let them decide

Tone: clear, neutral, respectful of the reader's intelligence."""


async def explanation_writer(state: PipelineState) -> PipelineState:
    log = state.get("agent_log", [])
    errors = state.get("errors", [])

    claim = state.get("primary_claim", "")
    verdict = state.get("verdict", {})
    supporting = state.get("supporting_evidence", [])
    contradicting = state.get("contradicting_evidence", [])
    contradiction_summary = state.get("contradiction_summary", "")

    log.append("ExplanationWriter: Drafting plain-language explanation...")

    def fmt_top(items: list, n: int = 3) -> str:
        return "\n".join([
            f"- {e['source_domain']}: {e['snippet'][:200]}"
            for e in items[:n]
        ]) or "None."

    prompt = f"""Claim: {claim}

Verdict: {verdict.get('label', 'Unverified')} (confidence: {verdict.get('confidence', 0):.0%})
Verdict Summary: {verdict.get('summary', '')}

Top Supporting Evidence:
{fmt_top(supporting)}

Top Contradicting Evidence:
{fmt_top(contradicting)}

Evidence Conflicts: {contradiction_summary}

Write the explanation."""

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        explanation = response.content.strip()
        log.append("ExplanationWriter: Explanation complete.")

    except Exception as e:
        errors.append(f"ExplanationWriter error: {str(e)}")
        explanation = (
            f"TruthLens AI investigated the claim: \"{claim}\". "
            f"The verdict is {verdict.get('label', 'Unverified')} with "
            f"{verdict.get('confidence', 0):.0%} confidence. "
            "A detailed explanation could not be generated due to a processing error."
        )

    return {
        **state,
        "explanation": explanation,
        "agent_log": log,
        "errors": errors,
    }
