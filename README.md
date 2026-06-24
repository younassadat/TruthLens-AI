# TruthLens AI

> Every claim deserves evidence.

AI-powered misinformation investigation platform built for **QuantumHacks 2026**.

---

## Stack

| Layer | Technology |
|-------|-----------|
| AI Orchestration | LangGraph (multi-agent DAG) |
| LLM Provider | Groq Cloud (free tier) |
| Heavy Reasoning | `llama-3.3-70b-versatile` |
| Balanced Tasks | `mixtral-8x7b-32768` |
| Fast Classification | `gemma2-9b-it` |
| Web Evidence | Tavily Search API |
| Backend | FastAPI + Python |
| Database | MongoDB Atlas |
| Frontend | React + Vite |

---

## Agent Pipeline

```
ClaimExtractor → EvidenceHunter → CredibilityScorer
                                         ↓
                             ContradictionDetector
                                         ↓
                              VerdictGenerator
                                         ↓
                              ExplanationWriter
```

---

## Quick Start

### 1. Get API Keys (both free)

- **Groq:** https://console.groq.com → create API key
- **Tavily:** https://tavily.com → sign up → get API key

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and add your keys
```

### 3. Run with Docker Compose

```bash
docker-compose up
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### 4. Run without Docker

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

### POST /verify
Full pipeline, synchronous response.
```json
{ "claim": "The Eiffel Tower was built in 1887." }
```

### POST /verify/stream
SSE stream — emits live agent progress events.
Events: `agent_start`, `agent_done`, `complete`, `error`

### GET /health
Health check.

---

## Project Structure

```
truthlens/
├── backend/
│   ├── agents/
│   │   ├── claim_extractor.py        # Agent 1 — llama-3.3-70b
│   │   ├── evidence_hunter.py        # Agent 2 — mixtral-8x7b + Tavily
│   │   ├── credibility_scorer.py     # Agent 3 — gemma2-9b
│   │   ├── contradiction_detector.py # Agent 4 — mixtral-8x7b
│   │   ├── verdict_generator.py      # Agent 5 — llama-3.3-70b
│   │   └── explanation_writer.py     # Agent 6 — llama-3.3-70b
│   ├── core/
│   │   ├── state.py                  # Shared TypedDict state
│   │   ├── llm.py                    # Groq model factory
│   │   └── pipeline.py               # LangGraph DAG
│   ├── api/
│   │   └── main.py                   # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       └── App.jsx                   # React dashboard
├── docker-compose.yml
└── README.md
```

---

## Team

- Technical Lead: Mr. Younas Sadat
- Co-founder: Yahya Sadat

**QuantumHacks 2026 · Submission Deadline: August 20, 2026**
