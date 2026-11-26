"""
diagnosis_llm.py  —  Level 3 : LLM narrative synthesis

Reads the L1 and L2 JSON results produced by the MAS (results/ directory),
builds a structured prompt, and calls Llama 3.2:3b via Ollama to produce
a plain-prose diagnostic narrative.

Usage:
    python diagnosis_llm.py
    python diagnosis_llm.py --mode aposteriori          # override mode (default: auto-detect)
    python diagnosis_llm.py --model mistral              # override Ollama model
    python diagnosis_llm.py --results-dir results/use_cases/DS11_.../aposteriori \
                            --out-dir     results/use_cases/DS11_.../aposteriori

--results-dir accepts either the live layout (<dir>/<family>/<mode>/*.json,
<dir>/level2/<mode>/*.json) or the archived per-use-case layout
(<dir>/level1/<family>/*.json, <dir>/level2/*.json).

Output (in --out-dir, default = --results-dir):
    l3_prompt.txt     — exact prompt sent to the LLM (written before the call)
    l3_narrative.txt  — LLM narrative
Exit code 0 on success, 2 if the Ollama call failed (l3_prompt.txt is kept).
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

# ── Config ────────────────────────────────────────────────────────────────────

OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL        = "llama3.2:3b"
PROJECT_ROOT = Path(__file__).resolve().parent
RESULTS_DIR  = PROJECT_ROOT / "results"
OUT_DIR      = None   # set from --out-dir (defaults to RESULTS_DIR)
FAMILIES     = ("structural", "dynamic", "functional", "procedural")

# ── CLI args ──────────────────────────────────────────────────────────────────

_parser = argparse.ArgumentParser(description="Level-3 LLM narrative synthesis")
_parser.add_argument("--results-dir", type=Path, default=None,
                     help="directory holding the L1/L2 JSON results (default: results/)")
_parser.add_argument("--mode", choices=("apriori", "aposteriori"), default=None,
                     help="mode (default: auto-detect)")
_parser.add_argument("--out-dir", type=Path, default=None,
                     help="where to write l3_prompt.txt / l3_narrative.txt (default: --results-dir)")
_parser.add_argument("--model", default=MODEL, help="Ollama model (default: llama3.2:3b)")
_cli, _ = _parser.parse_known_args()

MODEL = _cli.model
if _cli.results_dir is not None:
    RESULTS_DIR = _cli.results_dir.resolve()
OUT_DIR = (_cli.out_dir or RESULTS_DIR).resolve()
_mode_override = _cli.mode


def _is_archived_layout() -> bool:
    """True for results/use_cases/<DS>/<mode>/ (level1/<family>/, level2/*.json)."""
    return (RESULTS_DIR / "level1").is_dir()


def _l1_dir(family: str, mode: str) -> Path:
    if _is_archived_layout():
        return RESULTS_DIR / "level1" / family
    return RESULTS_DIR / family / mode


def _l2_dir(mode: str) -> Path:
    if _is_archived_layout():
        return RESULTS_DIR / "level2"
    return RESULTS_DIR / "level2" / mode

# ── Helpers ───────────────────────────────────────────────────────────────────

def _local_name(uri: str) -> str:
    return uri.rstrip("/").split("/")[-1].split("#")[-1]


def _detect_mode() -> str:
    """Infer mode from which results subdirectory has content."""
    if _is_archived_layout():
        ctx = RESULTS_DIR / "run_context.json"
        if ctx.exists():
            try:
                return json.loads(ctx.read_text(encoding="utf-8"))["mode"]
            except Exception:
                pass
        return RESULTS_DIR.name if RESULTS_DIR.name in ("apriori", "aposteriori") else "aposteriori"
    for mode in ("aposteriori", "apriori"):
        d = RESULTS_DIR / "level2" / mode
        if d.exists() and any(d.glob("*.json")):
            return mode
    return "aposteriori"


def load_l1_results(mode: str) -> dict[str, list]:
    """Return {agent_stem: [records]} for all active L1 agents of this mode."""
    active = {}
    for family in FAMILIES:
        d = _l1_dir(family, mode)
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
    d = _l2_dir(mode)
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

def run() -> int:
    mode = _mode_override or _detect_mode()
    print(f"[LLM] Mode: {mode}")
    print(f"[LLM] Results dir: {RESULTS_DIR}")

    l1 = load_l1_results(mode)
    l2 = load_l2_results(mode)

    print(f"[LLM] L1 active agents : {len(l1)}")
    print(f"[LLM] L2 triggered     : {len(l2)}")

    prompt = build_prompt(l1, l2, mode)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file    = OUT_DIR / "l3_prompt.txt"
    narrative_file = OUT_DIR / "l3_narrative.txt"

    # The exact prompt is saved before the call, so it survives an LLM failure.
    prompt_file.write_text(
        prompt if prompt is not None else "(no prompt: no L1 alert and no L2 diagnosis — LLM not called)\n",
        encoding="utf-8")

    if prompt is None:
        narrative = "No anomalies detected — the network graph appears healthy."
        print("[LLM] Nothing to analyse.")
    else:
        try:
            narrative = call_ollama(prompt)
        except Exception as e:
            print(f"[LLM] ERROR: Ollama call failed: {type(e).__name__}: {e}", file=sys.stderr)
            if narrative_file.exists():
                narrative_file.unlink()
            return 2

    narrative_file.write_text(narrative + "\n", encoding="utf-8")

    # Print to console
    print("\n" + "=" * 64)
    print("  DIAGNOSTIC NARRATIVE")
    print("=" * 64)
    print(narrative)
    print("=" * 64 + "\n")
    print(f"[LLM] Wrote {prompt_file} and {narrative_file}")
    return 0


if __name__ == "__main__":
    sys.exit(run())
