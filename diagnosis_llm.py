"""
diagnosis_llm.py  —  Level 3 : LLM narrative synthesis

Reads the L1 and L2 JSON results produced by the MAS (results/ directory),
builds a structured prompt, and calls Llama 3.2:3b via Ollama to produce
a plain-prose diagnostic narrative.

Usage:
    python diagnosis_llm.py
    python diagnosis_llm.py --mode aposteriori   # override mode (default: auto-detect)
    python diagnosis_llm.py --model mistral       # override Ollama model

Output:
    diagnostic_report.txt   — narrative appended with timestamp
"""

import json
import sys
import time
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_URL   = "http://localhost:11434/api/generate"
MODEL        = "llama3.2:3b"
PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_DIR  = PROJECT_ROOT / "results"
REPORT_FILE  = PROJECT_ROOT / "diagnostic_report.txt"

# ── CLI args ──────────────────────────────────────────────────────────────────

_args = sys.argv[1:]
for i, a in enumerate(_args):
    if a == "--model" and i + 1 < len(_args):
        MODEL = _args[i + 1]

_mode_override = None
for i, a in enumerate(_args):
    if a == "--mode" and i + 1 < len(_args):
        _mode_override = _args[i + 1]

# ── Helpers ───────────────────────────────────────────────────────────────────

def _local_name(uri: str) -> str:
    return uri.rstrip("/").split("/")[-1].split("#")[-1]


def _detect_mode() -> str:
    """Infer mode from which results subdirectory has content."""
    for mode in ("aposteriori", "apriori"):
        d = RESULTS_DIR / "level2" / mode
        if d.exists() and any(d.glob("*.json")):
            return mode
    return "aposteriori"


def load_l1_results(mode: str) -> dict[str, list]:
    """Return {agent_stem: [records]} for all active L1 agents of this mode."""
    active = {}
    for family in ("structural", "dynamic", "functional", "procedural"):
        d = RESULTS_DIR / family / mode
        if not d.exists():
            continue
        for path in sorted(d.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list) and data:
                    active[path.stem] = data
            except Exception:
                pass
    return active


def load_l2_results(mode: str) -> dict[str, dict]:
    """Return {agent_stem: result_dict} for triggered L2 diagnosers."""
    triggered = {}
    d = RESULTS_DIR / "level2" / mode
    if not d.exists():
        return triggered
    for path in sorted(d.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("activation_status") == "triggered":
                triggered[path.stem] = data
        except Exception:
            pass
    return triggered


def _uri_values(record: dict) -> list[str]:
    """Extract all URI local names from a SPARQL binding record."""
    names = []
    for v in record.values():
        if isinstance(v, dict) and v.get("type") == "uri":
            names.append(_local_name(v["value"]))
        elif isinstance(v, str) and v.startswith("http"):
            names.append(_local_name(v))
    return names


# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(l1: dict[str, list], l2: dict[str, dict], mode: str) -> str | None:
    if not l1 and not l2:
        return None

    lines = [
        "You are a network operations expert analyzing an ICT infrastructure.",
        "Based on the following automated detection results from a knowledge graph,",
        "write a concise technical diagnostic report in 3 to 5 sentences.",
        "Use the exact resource identifiers from the data.",
        "State the most critical issue first, explain which entities are affected,",
        "and give one concrete recommended action.",
        "Write plain prose — no bullet points, no headings.",
        "",
    ]

    # Block 1 — Level-1 alerts
    if l1:
        lines.append(f"=== LEVEL-1 ALERTS ({mode}) ===")
        for agent, records in sorted(l1.items()):
            entities = []
            for rec in records:
                entities.extend(_uri_values(rec))
            entities = list(dict.fromkeys(entities))[:6]
            label = agent.replace("_detector", "").replace("_", " ")
            lines.append(f"  [{label}]  {', '.join(entities)}")
        lines.append("")

    # Block 2 — Level-2 diagnoses
    if l2:
        lines.append(f"=== LEVEL-2 DIAGNOSES ({mode}) ===")
        for agent, result in sorted(
            l2.items(),
            key=lambda kv: -(kv[1].get("diagnoses") or [{}])[0].get("priority_score", 0),
        ):
            diagnoses = result.get("diagnoses", [])
            if not diagnoses:
                continue
            d = diagnoses[0]
            anchor = _local_name(d.get("target_id", "?"))
            rel  = d.get("reliability_score", "?")
            sev  = d.get("severity_score", "?")
            pri  = d.get("priority_score", "?")
            expl = d.get("explanation", "")
            label = agent.replace("_diagnoser", "").replace("_", " ")
            lines.append(f"  [{label}]  anchor={anchor}  "
                         f"reliability={rel}  severity={sev}  priority={pri}")
            if expl:
                lines.append(f"    → {expl}")
        lines.append("")

    lines.append("Diagnostic narrative:")
    return "\n".join(lines)


# ── LLM call ─────────────────────────────────────────────────────────────────

def call_ollama(prompt: str) -> str:
    print(f"[LLM] Calling Ollama ({MODEL})...", flush=True)
    t0 = time.perf_counter()
    r = requests.post(
        OLLAMA_URL,
        json={"model": MODEL, "prompt": prompt, "stream": False,
              "options": {"temperature": 0.1, "num_predict": 300}},
        timeout=120,
    )
    r.raise_for_status()
    elapsed = time.perf_counter() - t0
    text = r.json()["response"].strip()
    print(f"[LLM] Done in {elapsed:.1f}s  ({len(text)} chars)")
    return text


# ── Main ─────────────────────────────────────────────────────────────────────

def run():
    mode = _mode_override or _detect_mode()
    print(f"[LLM] Mode: {mode}")

    l1 = load_l1_results(mode)
    l2 = load_l2_results(mode)

    print(f"[LLM] L1 active agents : {len(l1)}")
    print(f"[LLM] L2 triggered     : {len(l2)}")

    prompt = build_prompt(l1, l2, mode)

    if prompt is None:
        narrative = "No anomalies detected — the network graph appears healthy."
        print("[LLM] Nothing to analyse.")
    else:
        narrative = call_ollama(prompt)

    # Print to console
    print("\n" + "=" * 64)
    print("  DIAGNOSTIC NARRATIVE")
    print("=" * 64)
    print(narrative)
    print("=" * 64 + "\n")

    # Append to report file with timestamp
    from datetime import datetime
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with REPORT_FILE.open("a", encoding="utf-8") as f:
        f.write(f"\n{'='*64}\n")
        f.write(f"  Run: {ts}  |  Mode: {mode}  |  Model: {MODEL}\n")
        f.write(f"  L1 active: {len(l1)}  |  L2 triggered: {len(l2)}\n")
        f.write(f"{'='*64}\n")
        f.write(narrative + "\n")
    print(f"[LLM] Report appended to {REPORT_FILE.name}")


if __name__ == "__main__":
    run()
