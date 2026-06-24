"""
Agent 2 — EvidenceHunter
Model: mixtral-8x7b-32768 (balanced) + Tavily Search API
Job: Generate smart search queries → fetch evidence from the web → structure results
"""

import json
import os
from urllib.parse import urlparse
from tavily import AsyncTavilyClient
from core.state import PipelineState
from core.llm import get_llm

llm = get_llm("balanced")


QUERY_SYSTEM_PROMPT = """You are a research assistant generating search queries for fact-checking.

Given a factual claim, generate 2-3 targeted search queries to find evidence.
Queries should:
- Be specific and targeted
- Cover different angles (supporting AND potentially contradicting)
- Use journalistic or academic phrasing

Return ONLY valid JSON:
{"queries": ["query 1", "query 2", "query 3"]}"""


async def evidence_hunter(state: PipelineState) -> PipelineState:
    log = state.get("agent_log", [])
    errors = state.get("errors", [])
    primary_claim = state.get("primary_claim", state["raw_input"])

    log.append("EvidenceHunter: Generating search queries...")

    # Step 1: Generate smart queries via LLM
    try:
        response = await llm.ainvoke([
            {"role": "system", "content": QUERY_SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate search queries to fact-check: {primary_claim}"}
        ])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        queries = json.loads(raw.strip()).get("queries", [primary_claim])
    except Exception as e:
        errors.append(f"EvidenceHunter query gen error: {str(e)}")
        queries = [primary_claim]

    log.append(f"EvidenceHunter: Searching with {len(queries)} queries...")

    # Step 2: Run Tavily searches
    tavily_key = os.getenv("TAVILY_API_KEY")
    if not tavily_key:
        errors.append("EvidenceHunter: TAVILY_API_KEY not set")
        return {**state, "evidence": [], "agent_log": log, "errors": errors}

    client = AsyncTavilyClient(api_key=tavily_key)
    all_evidence = []
    seen_urls = set()

    for query in queries:
        try:
            results = await client.search(
                query=query,
                max_results=4,
                include_raw_content=False,
                search_depth="advanced",
            )
            for r in results.get("results", []):
                url = r.get("url", "")
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                domain = urlparse(url).netloc.replace("www.", "")
                all_evidence.append({
                    "title": r.get("title", ""),
                    "url": url,
                    "snippet": r.get("content", "")[:500],
                    "source_domain": domain,
                    "credibility_score": 0.0,
                    "supports_claim": True,
                })
        except Exception as e:
            errors.append(f"EvidenceHunter search error for '{query}': {str(e)}")

    log.append(f"EvidenceHunter: Retrieved {len(all_evidence)} unique sources.")

    return {
        **state,
        "evidence": all_evidence,
        "agent_log": log,
        "errors": errors,
    }
