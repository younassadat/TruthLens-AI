import { useState, useRef } from "react";

// ── Design tokens ──────────────────────────────────────────────────────────────
// Palette: deep slate navy base, teal accent, amber for warnings, red for false
const VERDICT_CONFIG = {
  "True":           { color: "#10B981", bg: "#ECFDF5", label: "TRUE",           icon: "✓" },
  "False":          { color: "#EF4444", bg: "#FEF2F2", label: "FALSE",          icon: "✗" },
  "Misleading":     { color: "#F59E0B", bg: "#FFFBEB", label: "MISLEADING",     icon: "⚠" },
  "Partially True": { color: "#3B82F6", bg: "#EFF6FF", label: "PARTIALLY TRUE", icon: "◑" },
  "Unverified":     { color: "#8B5CF6", bg: "#F5F3FF", label: "UNVERIFIED",     icon: "?" },
};

const AGENTS = [
  { id: "claim_extractor",        label: "Claim Extractor",        desc: "Isolating verifiable facts",       icon: "🔍" },
  { id: "evidence_hunter",        label: "Evidence Hunter",        desc: "Searching trusted sources",        icon: "🌐" },
  { id: "credibility_scorer",     label: "Credibility Scorer",     desc: "Rating source trustworthiness",   icon: "⚖️" },
  { id: "contradiction_detector", label: "Contradiction Detector", desc: "Cross-examining evidence",         icon: "⚡" },
  { id: "verdict_generator",      label: "Verdict Generator",      desc: "Synthesizing findings",            icon: "📋" },
  { id: "explanation_writer",     label: "Explanation Writer",     desc: "Drafting plain-language summary",  icon: "✍️" },
];

// ── Credibility bar ────────────────────────────────────────────────────────────
function CredBar({ score }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.8 ? "#10B981" : score >= 0.5 ? "#F59E0B" : "#EF4444";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
      <div style={{ flex: 1, height: 6, background: "#E2E8F0", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 3, transition: "width 0.5s ease" }} />
      </div>
      <span style={{ fontSize: 11, color: "#64748B", minWidth: 28 }}>{pct}%</span>
    </div>
  );
}

// ── Evidence card ──────────────────────────────────────────────────────────────
function EvidenceCard({ item, type }) {
  const isSupporting = type === "supporting";
  return (
    <div style={{
      border: `1px solid ${isSupporting ? "#BBF7D0" : "#FECACA"}`,
      background: isSupporting ? "#F0FDF4" : "#FFF5F5",
      borderRadius: 10,
      padding: "12px 14px",
      marginBottom: 8,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 4 }}>
        <a href={item.url} target="_blank" rel="noreferrer"
           style={{ fontSize: 13, fontWeight: 600, color: "#1E293B", textDecoration: "none", flex: 1, marginRight: 8, lineHeight: 1.3 }}>
          {item.title || item.source_domain}
        </a>
        <span style={{
          fontSize: 10, fontWeight: 700, padding: "2px 7px", borderRadius: 20,
          color: isSupporting ? "#065F46" : "#991B1B",
          background: isSupporting ? "#D1FAE5" : "#FEE2E2",
          whiteSpace: "nowrap"
        }}>
          {isSupporting ? "SUPPORTS" : "CONTRADICTS"}
        </span>
      </div>
      <p style={{ fontSize: 12, color: "#64748B", margin: "0 0 8px", lineHeight: 1.5 }}>{item.snippet?.slice(0, 200)}…</p>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 11, color: "#94A3B8" }}>{item.source_domain}</span>
        <div style={{ width: 120 }}><CredBar score={item.credibility_score || 0} /></div>
      </div>
    </div>
  );
}

// ── Agent pipeline feed ────────────────────────────────────────────────────────
function AgentFeed({ activeAgent, completedAgents, agentLogs }) {
  return (
    <div style={{ fontFamily: "monospace" }}>
      {AGENTS.map((agent, i) => {
        const isDone    = completedAgents.includes(agent.id);
        const isActive  = activeAgent === agent.id;
        const isPending = !isDone && !isActive;
        const log       = agentLogs[agent.id];

        return (
          <div key={agent.id} style={{
            display: "flex", alignItems: "flex-start", gap: 12,
            padding: "10px 0",
            borderBottom: i < AGENTS.length - 1 ? "1px solid #F1F5F9" : "none",
            opacity: isPending ? 0.35 : 1,
            transition: "opacity 0.3s ease",
          }}>
            {/* Status indicator */}
            <div style={{
              width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 13,
              background: isDone ? "#D1FAE5" : isActive ? "#DBEAFE" : "#F1F5F9",
              border: `2px solid ${isDone ? "#10B981" : isActive ? "#3B82F6" : "#E2E8F0"}`,
              animation: isActive ? "pulse 1.2s ease-in-out infinite" : "none",
            }}>
              {isDone ? "✓" : isActive ? "⋯" : agent.icon}
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
                <span style={{ fontSize: 13, fontWeight: 700, color: "#1E293B" }}>{agent.label}</span>
                {isActive && (
                  <span style={{ fontSize: 10, color: "#3B82F6", fontWeight: 600,
                    background: "#EFF6FF", padding: "1px 6px", borderRadius: 10 }}>
                    RUNNING
                  </span>
                )}
                {isDone && (
                  <span style={{ fontSize: 10, color: "#10B981", fontWeight: 600,
                    background: "#ECFDF5", padding: "1px 6px", borderRadius: 10 }}>
                    DONE
                  </span>
                )}
              </div>
              <p style={{ fontSize: 11, color: "#94A3B8", margin: 0 }}>
                {log || agent.desc}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Confidence meter ───────────────────────────────────────────────────────────
function ConfidenceMeter({ score }) {
  const pct = Math.round(score * 100);
  const color = score >= 0.75 ? "#10B981" : score >= 0.5 ? "#F59E0B" : "#EF4444";
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div style={{ textAlign: "center" }}>
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="#E2E8F0" strokeWidth="8" />
        <circle cx="50" cy="50" r="40" fill="none" stroke={color} strokeWidth="8"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
          style={{ transition: "stroke-dashoffset 1s ease" }}
        />
        <text x="50" y="55" textAnchor="middle" fontSize="18" fontWeight="700" fill="#1E293B">{pct}%</text>
      </svg>
      <div style={{ fontSize: 11, color: "#64748B", marginTop: -4 }}>Confidence</div>
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────────
export default function App() {
  const [claim, setClaim] = useState("");
  const [status, setStatus] = useState("idle"); // idle | running | done | error
  const [result, setResult] = useState(null);
  const [activeAgent, setActiveAgent] = useState(null);
  const [completedAgents, setCompletedAgents] = useState([]);
  const [agentLogs, setAgentLogs] = useState({});
  const [errorMsg, setErrorMsg] = useState("");
  const eventSourceRef = useRef(null);

  const API = "http://localhost:8000";

  const handleVerify = async () => {
    if (!claim.trim()) return;

    // Reset state
    setStatus("running");
    setResult(null);
    setActiveAgent(null);
    setCompletedAgents([]);
    setAgentLogs({});
    setErrorMsg("");

    if (eventSourceRef.current) eventSourceRef.current.close();

    try {
      const response = await fetch(`${API}/verify/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claim }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value);
        const lines = text.split("\n");

        for (const line of lines) {
          if (!line.startsWith("data:")) continue;
          try {
            const event = JSON.parse(line.slice(5).trim());

            if (event.event === "agent_start") {
              setActiveAgent(event.agent);
            } else if (event.event === "agent_done") {
              setActiveAgent(null);
              setCompletedAgents(prev => [...prev, event.agent]);
              if (event.log) {
                setAgentLogs(prev => ({ ...prev, [event.agent]: event.log }));
              }
            } else if (event.event === "complete") {
              setResult(event.data);
              setStatus("done");
              setActiveAgent(null);
            } else if (event.event === "error") {
              setErrorMsg(event.message || "Unknown error");
              setStatus("error");
            }
          } catch {}
        }
      }
    } catch (err) {
      setErrorMsg(err.message);
      setStatus("error");
    }
  };

  const verdictCfg = result ? VERDICT_CONFIG[result.verdict?.label] || VERDICT_CONFIG["Unverified"] : null;

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0F172A",
      fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif",
      color: "#1E293B",
    }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
        * { box-sizing: border-box; }
        textarea:focus { outline: none; }
        button:hover:not(:disabled) { filter: brightness(1.08); }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .fade-in { animation: fadeIn 0.4s ease both; }
      `}</style>

      {/* Header */}
      <div style={{ background: "#0F172A", borderBottom: "1px solid #1E293B", padding: "0 24px" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", alignItems: "center", height: 60, gap: 12 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: "linear-gradient(135deg, #0D9488, #3B82F6)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 16,
          }}>🔎</div>
          <span style={{ fontSize: 18, fontWeight: 800, color: "#F8FAFC", letterSpacing: "-0.3px" }}>
            TruthLens <span style={{ color: "#0D9488" }}>AI</span>
          </span>
          <span style={{ fontSize: 12, color: "#475569", marginLeft: 4 }}>
            Every claim deserves evidence.
          </span>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 24px" }}>

        {/* Hero input */}
        <div style={{
          background: "#1E293B", borderRadius: 16, padding: 24, marginBottom: 28,
          border: "1px solid #334155",
        }}>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#F8FAFC", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
            Investigate a Claim
          </h1>
          <p style={{ fontSize: 13, color: "#64748B", margin: "0 0 16px" }}>
            Submit any claim, article excerpt, or viral statement. TruthLens will investigate it with 6 specialized AI agents.
          </p>
          <textarea
            value={claim}
            onChange={e => setClaim(e.target.value)}
            placeholder='e.g. "Scientists have confirmed that coffee prevents Alzheimer\'s disease."'
            disabled={status === "running"}
            rows={3}
            style={{
              width: "100%", padding: "12px 14px",
              background: "#0F172A", border: "1px solid #334155",
              borderRadius: 10, fontSize: 14, color: "#F1F5F9",
              resize: "vertical", lineHeight: 1.6,
            }}
          />
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12, gap: 10 }}>
            {status !== "idle" && (
              <button onClick={() => { setStatus("idle"); setResult(null); setClaim(""); }}
                style={{
                  padding: "10px 20px", background: "#334155", color: "#94A3B8",
                  border: "none", borderRadius: 8, fontSize: 13, cursor: "pointer", fontWeight: 600,
                }}>
                Reset
              </button>
            )}
            <button
              onClick={handleVerify}
              disabled={status === "running" || !claim.trim()}
              style={{
                padding: "10px 24px",
                background: status === "running"
                  ? "#1E293B"
                  : "linear-gradient(135deg, #0D9488, #0891B2)",
                color: "#FFFFFF",
                border: status === "running" ? "1px solid #334155" : "none",
                borderRadius: 8, fontSize: 13, cursor: "pointer",
                fontWeight: 700, letterSpacing: "0.3px",
                display: "flex", alignItems: "center", gap: 8,
              }}>
              {status === "running" ? (
                <><span style={{ animation: "pulse 1s infinite" }}>⋯</span> Investigating…</>
              ) : "Investigate →"}
            </button>
          </div>
        </div>

        {/* Main content — 2 columns when results visible */}
        <div style={{
          display: "grid",
          gridTemplateColumns: (status === "running" || status === "done") ? "320px 1fr" : "1fr",
          gap: 24,
          alignItems: "start",
        }}>

          {/* Left: Agent pipeline */}
          {(status === "running" || status === "done") && (
            <div style={{
              background: "#FFFFFF", borderRadius: 14, padding: 20,
              border: "1px solid #E2E8F0",
            }} className="fade-in">
              <h2 style={{ fontSize: 13, fontWeight: 700, color: "#64748B", letterSpacing: "0.8px",
                textTransform: "uppercase", margin: "0 0 16px" }}>
                Investigation Pipeline
              </h2>
              <AgentFeed
                activeAgent={activeAgent}
                completedAgents={completedAgents}
                agentLogs={agentLogs}
              />
            </div>
          )}

          {/* Right: Results */}
          {status === "done" && result && (
            <div className="fade-in">

              {/* Verdict banner */}
              <div style={{
                background: verdictCfg.bg,
                border: `2px solid ${verdictCfg.color}`,
                borderRadius: 14, padding: "20px 24px", marginBottom: 20,
                display: "flex", alignItems: "center", gap: 20,
              }}>
                <ConfidenceMeter score={result.verdict?.confidence || 0} />
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                    <span style={{
                      fontSize: 24, fontWeight: 900, color: verdictCfg.color, letterSpacing: "-0.5px"
                    }}>
                      {verdictCfg.icon} {verdictCfg.label}
                    </span>
                  </div>
                  <p style={{ fontSize: 14, color: "#334155", margin: 0, lineHeight: 1.5 }}>
                    {result.verdict?.summary}
                  </p>
                  <p style={{ fontSize: 12, color: "#94A3B8", margin: "8px 0 0" }}>
                    Claim: <em>"{result.claim}"</em>
                  </p>
                </div>
              </div>

              {/* Explanation */}
              <div style={{
                background: "#FFFFFF", borderRadius: 14, padding: 20, marginBottom: 20,
                border: "1px solid #E2E8F0",
              }}>
                <h2 style={{ fontSize: 13, fontWeight: 700, color: "#64748B", letterSpacing: "0.8px",
                  textTransform: "uppercase", margin: "0 0 12px" }}>
                  Explanation
                </h2>
                {result.explanation.split("\n\n").map((para, i) => (
                  <p key={i} style={{ fontSize: 14, color: "#334155", lineHeight: 1.7, margin: "0 0 12px" }}>
                    {para}
                  </p>
                ))}
              </div>

              {/* Evidence */}
              <div style={{
                background: "#FFFFFF", borderRadius: 14, padding: 20,
                border: "1px solid #E2E8F0",
              }}>
                <h2 style={{ fontSize: 13, fontWeight: 700, color: "#64748B", letterSpacing: "0.8px",
                  textTransform: "uppercase", margin: "0 0 16px" }}>
                  Evidence ({(result.supporting_evidence?.length || 0) + (result.contradicting_evidence?.length || 0)} sources)
                </h2>

                {result.supporting_evidence?.length > 0 && (
                  <>
                    <h3 style={{ fontSize: 12, fontWeight: 700, color: "#065F46", marginBottom: 8 }}>
                      ✓ Supporting ({result.supporting_evidence.length})
                    </h3>
                    {result.supporting_evidence.slice(0, 4).map((item, i) => (
                      <EvidenceCard key={i} item={item} type="supporting" />
                    ))}
                  </>
                )}

                {result.contradicting_evidence?.length > 0 && (
                  <>
                    <h3 style={{ fontSize: 12, fontWeight: 700, color: "#991B1B", margin: "16px 0 8px" }}>
                      ✗ Contradicting ({result.contradicting_evidence.length})
                    </h3>
                    {result.contradicting_evidence.slice(0, 4).map((item, i) => (
                      <EvidenceCard key={i} item={item} type="contradicting" />
                    ))}
                  </>
                )}

                {result.contradiction_summary && (
                  <div style={{
                    background: "#FFFBEB", border: "1px solid #FDE68A",
                    borderRadius: 8, padding: 12, marginTop: 16,
                  }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: "#92400E" }}>CONFLICT ANALYSIS  </span>
                    <span style={{ fontSize: 12, color: "#78350F" }}>{result.contradiction_summary}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error state */}
          {status === "error" && (
            <div className="fade-in" style={{
              background: "#FEF2F2", border: "1px solid #FECACA",
              borderRadius: 14, padding: 20,
            }}>
              <h3 style={{ color: "#991B1B", margin: "0 0 8px" }}>Investigation Failed</h3>
              <p style={{ color: "#7F1D1D", fontSize: 13, margin: 0 }}>{errorMsg || "An unexpected error occurred."}</p>
              <p style={{ color: "#94A3B8", fontSize: 12, margin: "8px 0 0" }}>
                Check that your backend is running at {API} and your API keys are configured.
              </p>
            </div>
          )}

        </div>

        {/* Footer */}
        <div style={{ textAlign: "center", marginTop: 40, color: "#334155", fontSize: 11 }}>
          TruthLens AI · Powered by Groq (llama-3.3-70b · mixtral-8x7b · gemma2-9b) + LangGraph + Tavily
        </div>
      </div>
    </div>
  );
}
