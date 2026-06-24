"""
Agent 1 — ClaimExtractor
Model: llama-3.3-70b-versatile (heavy reasoning)
Job: Parse raw user input → extract verifiable factual claims → pick the primary claim
"""

import json
from core.state import PipelineState
from core.llm import get_llm

llm = get_llm("heavy")

SYSTEM_PROMPT = """You are a precise fact-checking assistant specializing in claim extraction.

Your job is to analyze user-submitted text and extract VERIFIABLE FACTUAL CLAIMS — statements that can be checked against evidence.

Rules:
- Only extract objective, checkable claims (not opinions or predictions)
- Rank them by checkability and public importance
- The primary_claim should be the single most important, most verifiable claim
- Return ONLY valid JSON, no preamble, no markdown fences

Output format:
{
  "claims": ["claim 1", "claim 2", ...],
  "primary_claim": "the single most verifiable and important claim"
}"""


async def claim_extractor(state: PipelineState) -> PipelineState:
    log = state.get("agent_log", [])
    errors = state.get("errors", [])

    log.append("ClaimExtractor: Analyzing input...")

    try:
        response = await llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Extract verifiable claims from this text:\n\n{state['raw_input']}"}
        ])

        raw = response.content.strip()
        # Strip markdown fences if model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())

        claims = parsed.get("claims", [])
        primary = parsed.get("primary_claim", claims[0] if claims else state["raw_input"])

        log.append(f"ClaimExtractor: Found {len(claims)} claim(s). Primary: \"{primary[:80]}...\"" if len(primary) > 80 else f"ClaimExtractor: Found {len(claims)} claim(s). Primary: \"{primary}\"")

        return {
            **state,
            "claims": claims,
            "primary_claim": primary,
            "agent_log": log,
            "errors": errors,
        }

    except Exception as e:
        errors.append(f"ClaimExtractor error: {str(e)}")
        log.append("ClaimExtractor: Failed to parse claims, using raw input as primary claim")
        return {
            **state,
            "claims": [state["raw_input"]],
            "primary_claim": state["raw_input"],
            "agent_log": log,
            "errors": errors,
        }
