"""
TruthLens AI — FastAPI Backend

Endpoints:
  POST /verify          → run full pipeline, return complete result
  POST /verify/stream   → SSE stream — emits agent progress events in real-time
  GET  /health          → health check
"""

import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

load_dotenv()

# Import pipeline after env is loaded
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.pipeline import run_pipeline
from core.state import PipelineState

app = FastAPI(
    title="TruthLens AI",
    description="AI-powered misinformation investigation platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VerifyRequest(BaseModel):
    claim: str

    class Config:
        json_schema_extra = {
            "example": {"claim": "The Eiffel Tower was built in 1887."}
        }


def format_result(state: PipelineState) -> dict:
    """Serialize final pipeline state into API response."""
    return {
        "claim": state.get("primary_claim", state["raw_input"]),
        "all_claims": state.get("claims", []),
        "verdict": state.get("verdict", {}),
        "explanation": state.get("explanation", ""),
        "supporting_evidence": state.get("supporting_evidence", []),
        "contradicting_evidence": state.get("contradicting_evidence", []),
        "avg_source_credibility": state.get("avg_source_credibility", 0.0),
        "contradiction_summary": state.get("contradiction_summary", ""),
        "agent_log": state.get("agent_log", []),
        "errors": state.get("errors", []),
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": "TruthLens AI"}


@app.post("/verify")
async def verify(request: VerifyRequest):
    """Run full pipeline synchronously and return complete result."""
    if not request.claim.strip():
        raise HTTPException(status_code=400, detail="Claim cannot be empty.")

    state = await run_pipeline(request.claim)
    return format_result(state)


@app.post("/verify/stream")
async def verify_stream(request: VerifyRequest):
    """
    SSE endpoint — streams agent progress events as the pipeline runs.
    Frontend watches this to animate the live investigation feed.

    Event types:
      agent_start   — an agent has begun
      agent_done    — an agent finished, partial state included
      complete      — full final result
      error         — pipeline error
    """
    if not request.claim.strip():
        raise HTTPException(status_code=400, detail="Claim cannot be empty.")

    AGENT_LABELS = {
        "claim_extractor":       "Extracting Claims",
        "evidence_hunter":       "Hunting Evidence",
        "credibility_scorer":    "Scoring Credibility",
        "contradiction_detector":"Detecting Contradictions",
        "verdict_generator":     "Generating Verdict",
        "explanation_writer":    "Writing Explanation",
    }

    async def event_generator():
        # We run the pipeline and stream intermediate state via a queue
        queue: asyncio.Queue = asyncio.Queue()

        async def run_with_hooks():
            """Wrap each agent with before/after events pushed to queue."""
            from core.llm import get_llm
            from agents.claim_extractor import claim_extractor
            from agents.evidence_hunter import evidence_hunter
            from agents.credibility_scorer import credibility_scorer
            from agents.contradiction_detector import contradiction_detector
            from agents.verdict_generator import verdict_generator
            from agents.explanation_writer import explanation_writer

            agents = [
                ("claim_extractor", claim_extractor),
                ("evidence_hunter", evidence_hunter),
                ("credibility_scorer", credibility_scorer),
                ("contradiction_detector", contradiction_detector),
                ("verdict_generator", verdict_generator),
                ("explanation_writer", explanation_writer),
            ]

            state: PipelineState = {
                "raw_input": request.claim,
                "claims": [], "primary_claim": "",
                "evidence": [], "scored_evidence": [],
                "avg_source_credibility": 0.0,
                "supporting_evidence": [], "contradicting_evidence": [],
                "contradiction_summary": "", "verdict": {},
                "explanation": "", "errors": [], "agent_log": [],
            }

            try:
                for agent_id, agent_fn in agents:
                    await queue.put({
                        "event": "agent_start",
                        "agent": agent_id,
                        "label": AGENT_LABELS.get(agent_id, agent_id),
                    })
                    state = await agent_fn(state)
                    await queue.put({
                        "event": "agent_done",
                        "agent": agent_id,
                        "label": AGENT_LABELS.get(agent_id, agent_id),
                        "log": state.get("agent_log", [])[-1] if state.get("agent_log") else "",
                    })

                # Final result
                await queue.put({
                    "event": "complete",
                    "data": format_result(state),
                })
            except Exception as e:
                await queue.put({"event": "error", "message": str(e)})
            finally:
                await queue.put(None)  # sentinel

        # Run pipeline in background
        asyncio.create_task(run_with_hooks())

        # Yield SSE events as they arrive
        while True:
            item = await queue.get()
            if item is None:
                break
            yield {"data": json.dumps(item)}

    return EventSourceResponse(event_generator())
