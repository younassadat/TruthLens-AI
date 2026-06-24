"""
TruthLens AI — Groq LLM factory.

Model assignments:
  llama-3.3-70b-versatile  → heavy reasoning (claim extraction, verdict, explanation)
  mixtral-8x7b-32768       → balanced tasks  (evidence search prompts, contradiction detection)
  gemma2-9b-it             → fast/light tasks (credibility scoring, classification)
"""

from langchain_groq import ChatGroq
import os


def get_llm(role: str = "heavy") -> ChatGroq:
    """
    role: "heavy" | "balanced" | "light"
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment")

    model_map = {
        "heavy":    "llama-3.3-70b-versatile",
        "balanced": "mixtral-8x7b-32768",
        "light":    "gemma2-9b-it",
    }

    return ChatGroq(
        model=model_map[role],
        api_key=api_key,
        temperature=0.1,   # low temp for factual tasks
        max_tokens=2048,
    )
