"""
Agent 3 — CredibilityScorer
Model: gemma2-9b-it (lightweight — fast classification per source)
Job: Score each source's trustworthiness (0.0–1.0) based on domain reputation,
     known bias, and content signals. Returns scored_evidence + avg_source_credibility.
"""

import json
import asyncio
from core.state import PipelineState
from core.llm import get_llm

llm = get_llm("light")

# Hardcoded baseline scores for well-known domains (avoids LLM calls for obvious cases)
DOMAIN_BASELINES: dict[str, float] = {
    # High credibility
    "reuters.com": 0.95, "apnews.com": 0.95, "bbc.com": 0.90, "bbc.co.uk": 0.90,
    "nytimes.com": 0.88, "washingtonpost.com": 0.87, "theguardian.com": 0.87,
    "npr.org": 0.88, "pbs.org": 0.87, "economist.com": 0.90,
    "nature.com": 0.97, "science.org": 0.97, "pubmed.ncbi.nlm.nih.gov": 0.98,
    "who.int": 0.93, "cdc.gov": 0.93, "nih.gov": 0.95,
    "snopes.com": 0.85, "factcheck.org": 0.85, "politifact.com": 0.84,
    "wikipedia.org": 0.70,
    # Lower credibility signals
    "infowars.com": 0.05, "naturalnews.com": 0.10, "breitbart.com": 0.30,
}

SYSTEM_PROMPT = """You are a media credibility analyst. Score the trustworthiness of a news source.

Consider:
- Domain type (.gov, .edu, .org, .com)
- Whether the snippet contains sensationalist language
- Presence of named authors, citations, dates
- Editorial standards signals

Return ONLY valid JSON:
{"score": 0.75, "reason": "one-sentence reason"}

Score from 0.0 (not credible) to 1.0 (highly credible)."""


async def score_single(item: dict) -> dict:
    domain = item["source_domain"]

    # Use baseline if we know this domain
    if domain in DOMAIN_BASELINES:
        item["credibility_score"] = DOMAIN_BASELINES[domain]
        return item

    # Otherwise ask gemma2-9b-it
    try:
        prompt = f"""Domain: {domain}
Title: {item['title']}
Snippet: {item['snippet'][:300]}

Score the credibility of this source."""
        response = await llm.ainvoke([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        item["credibility_score"] = float(parsed.get("score", 0.5))
    except Exception:
        item["credibility_score"] = 0.5  # neutral fallback

    return item


async def credibility_scorer(state: PipelineState) -> PipelineState:
    log = state.get("agent_log", [])
    errors = state.get("errors", [])
    evidence = state.get("evidence", [])

    log.append(f"CredibilityScorer: Scoring {len(evidence)} sources...")

    if not evidence:
        log.append("CredibilityScorer: No evidence to score.")
        return {**state, "scored_evidence": [], "avg_source_credibility": 0.0, "agent_log": log, "errors": errors}

    # Score all sources concurrently
    scored = await asyncio.gather(*[score_single(dict(item)) for item in evidence])
    scored = list(scored)

    avg = sum(s["credibility_score"] for s in scored) / len(scored)
    log.append(f"CredibilityScorer: Average source credibility = {avg:.2f}")

    return {
        **state,
        "scored_evidence": scored,
        "avg_source_credibility": round(avg, 3),
        "agent_log": log,
        "errors": errors,
    }
