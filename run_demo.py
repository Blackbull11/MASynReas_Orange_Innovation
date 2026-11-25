"""
run_demo.py  —  Demo setup for MASynReas soutenance

Loads a dataset into Virtuoso and updates mas.properties so the system
is ready for a live demo (gradlew run → diagnosis_llm.py).

Usage:
    python run_demo.py              # DS11  SPOF aposteriori  (recommended)
    python run_demo.py DS18         # Mixed two diagnoses aposteriori
    python run_demo.py DS04         # Structural fragility apriori
    python run_demo.py noria        # noria-0.2  (must be in Virtuoso dumps folder)
    python run_demo.py DS11 --mode aposteriori   # explicit mode override
"""

from __future__ import annotations
import sys
import time
from pathlib import Path

import requests
from requests.auth import HTTPDigestAuth

# ── Config ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent
DATASETS_DIR = PROJECT_ROOT / "datasets"
PROPS_FILE   = PROJECT_ROOT / "mas.properties"
PYTHON_PATH  = "C:/Users/paulc/AppData/Local/Programs/Python/Python313/python.exe"

NORIA_DUMPS  = Path("C:/Program Files/OpenLink Software/Virtuoso OpenSource 7.2/database/dumps")
CRUD_URL     = "http://localhost:8890/sparql-graph-crud-auth"
SPARQL_URL   = "http://localhost:8890/sparql"
AUTH         = HTTPDigestAuth("dba", "dba")
DS_GRAPH     = "http://dataset/"
NR_GRAPH     = "http://noria/"
OLLAMA_URL   = "http://localhost:11434/api/tags"

# Apriori datasets
APRIORI_IDS = {"DS01", "DS02", "DS03", "DS04", "DS05", "DS06",
               "DS07", "DS08", "DS09", "DS10", "DS24", "DS25", "DS26", "DS27"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def _resolve_dataset(short: str) -> tuple[str, Path]:
    """Return (full_name, ttl_path) for a short ID like 'DS11'."""
    matches = sorted(DATASETS_DIR.glob(f"{short}*"))
    if not matches:
        raise FileNotFoundError(f"No dataset matching '{short}' in {DATASETS_DIR}")
    name = matches[0].name
    ttl  = matches[0] / "dataset.ttl"
    if not ttl.exists():
        raise FileNotFoundError(f"{ttl} not found")
    return name, ttl


def _infer_mode(dataset_id: str) -> str:
    prefix = dataset_id.split("_")[0]  # "DS11" etc.
    return "apriori" if prefix in APRIORI_IDS else "aposteriori"


def _http_put(ttl_path: Path, graph: str, replace: bool = True) -> None:
    fn = requests.put if replace else requests.post
    r = fn(CRUD_URL, params={"graph": graph}, data=ttl_path.read_bytes(),
           headers={"Content-Type": "text/turtle"}, auth=AUTH, timeout=60)
    if r.status_code not in (200, 201, 204):
        print(f"  WARN HTTP {r.status_code}: {r.text[:120]}")


def _count_triples() -> int:
    try:
        r = requests.get(SPARQL_URL, params={
            "query": "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }",
            "format": "application/sparql-results+json",
        }, timeout=10)
        bindings = r.json()["results"]["bindings"]
        return int(bindings[0]["n"]["value"]) if bindings else -1
    except Exception:
        return -1


def _check_service(url: str, label: str) -> bool:
    try:
        requests.get(url, timeout=5)
        print(f"  [OK]  {label}")
        return True
    except Exception:
        print(f"  [!!]  {label} — NOT REACHABLE")
        return False


def _update_mas_properties(mode: str, dataset_id: str) -> None:
    lines = PROPS_FILE.read_text(encoding="utf-8").splitlines()
    updated = []
    for line in lines:
        if line.startswith("mode="):
            updated.append(f"mode={mode}")
        elif line.startswith("dataset.id="):
            updated.append(f"dataset.id={dataset_id}")
        elif line.startswith("python.path="):
            updated.append(f"python.path={PYTHON_PATH}")
        else:
            updated.append(line)
    PROPS_FILE.write_text("\n".join(updated) + "\n", encoding="utf-8")

# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    use_noria = "noria" in args
    mode_override = None
    if "--mode" in args:
        idx = args.index("--mode")
        if idx + 1 < len(args):
            mode_override = args[idx + 1]

    ds_arg = next((a for a in args if a.startswith("DS")), "DS11")

    print(f"\n{'='*62}")
    print(f"  MASynReas DEMO SETUP")
    print(f"{'='*62}")

    # ── Step 1: check services ────────────────────────────────────────────────
    print("\n[1/3] Checking services...")
    v_ok = _check_service(SPARQL_URL + "?query=ASK{}", "Virtuoso  http://localhost:8890")
    o_ok = _check_service(OLLAMA_URL, "Ollama    http://localhost:11434")

    if not v_ok:
        print("\n  Virtuoso must be running before the demo.")
        print("  Start it from the Virtuoso Conductor or its system service.")
        sys.exit(1)
    if not o_ok:
        print("\n  WARNING: Ollama is not running.")
        print("  diagnosis_llm.py (Level 3) will fail unless Ollama is started.")
        print("  Start it with:  ollama serve")

    # ── Step 2: load data into Virtuoso ───────────────────────────────────────
    print("\n[2/3] Loading data into Virtuoso...")

    if use_noria:
        dataset_id = "noria_0.2"
        mode = mode_override or "aposteriori"
        # Load noria dumps (PUT first file, POST the rest)
        ttl_files = sorted(NORIA_DUMPS.glob("*.ttl"))
        if not ttl_files:
            print(f"  ERROR: no .ttl files in {NORIA_DUMPS}")
            sys.exit(1)
        for i, ttl in enumerate(ttl_files):
            _http_put(ttl, NR_GRAPH, replace=(i == 0))
            print(f"  Loaded {ttl.name}")
    else:
        try:
            dataset_id, ttl_path = _resolve_dataset(ds_arg)
        except FileNotFoundError as e:
            print(f"  ERROR: {e}")
            sys.exit(1)
        mode = mode_override or _infer_mode(dataset_id)
        # Delete current dataset graph, then load
        requests.delete(CRUD_URL, params={"graph": DS_GRAPH}, auth=AUTH, timeout=10)
        _http_put(ttl_path, DS_GRAPH, replace=True)
        print(f"  Loaded {dataset_id}/dataset.ttl → graph <{DS_GRAPH}>")

    n = _count_triples()
    print(f"  Virtuoso now has {n} triples total")

    # ── Step 3: update mas.properties ────────────────────────────────────────
    print("\n[3/3] Updating mas.properties...")
    _update_mas_properties(mode, dataset_id)
    print(f"  mode       = {mode}")
    print(f"  dataset.id = {dataset_id}")
    print(f"  python.path = {PYTHON_PATH}")

    # ── Ready ─────────────────────────────────────────────────────────────────
    print(f"\n{'='*62}")
    print(f"  READY — run the demo in order:")
    print(f"")
    print(f"    Step 1 (L1 + L2):   gradlew run")
    print(f"    Step 2 (L3):        python diagnosis_llm.py")
    print(f"")
    print(f"  Expected L2 output → results/level2/{mode}/")
    print(f"  Narrative           → diagnostic_report.txt")
    print(f"{'='*62}\n")


if __name__ == "__main__":
    main()
