"""
run_use_cases.py  —  Run L1 + L2 (+ L3) on every (dataset, mode) pair of the
synthetic catalogue and archive each run in results/use_cases/<DS>/<mode>/.

JaCaMo is NOT involved: the L1 detectors and L2 diagnosers (src/agt/**/*.py)
are called directly, as evaluate_datasets.py does, with these corrections:
  - every user graph is dropped before loading a dataset (the detectors query
    the default graph = union of all graphs), and the loaded triple count is
    checked against eval_results.json;
  - the live result folders of the mode are purged before each run, so a
    failing script can never leave a stale JSON from the previous dataset;
  - per-script timeout, TimeoutExpired caught, return code / duration / output
    file recorded; a failing L1 blocks L2 and marks the run invalid;
  - L1 metrics compare NON-EMPTY detector outputs to expected_level1.json
    (not return codes).

Only the Virtuoso Docker container is used (HTTP endpoints on localhost:8890);
the Windows service Virtuoso_vos is never started.

Usage:
    python -X utf8 run_use_cases.py                       # all 36 pairs
    python -X utf8 run_use_cases.py DS11:aposteriori DS01:apriori
    python -X utf8 run_use_cases.py DS19                  # both modes of DS19
    python -X utf8 run_use_cases.py --skip-l3 ...

Configuration (argument > environment variable > default):
    --sparql-url   MASYN_SPARQL_URL         http://localhost:8890/sparql
    --crud-url     MASYN_CRUD_URL           http://localhost:8890/sparql-graph-crud-auth
    --user         MASYN_VIRTUOSO_USER      dba
    --password     MASYN_VIRTUOSO_PASSWORD  dba
    --container    MASYN_VIRTUOSO_CONTAINER openlinkvirtuoso
    --noria-dumps  MASYN_NORIA_DUMPS        C:/Program Files/OpenLink Software/Virtuoso OpenSource 7.2/database/dumps
    --python       MASYN_PYTHON             (this interpreter)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from requests.auth import HTTPDigestAuth

PROJECT_ROOT  = Path(__file__).resolve().parent
DATASETS_DIR  = PROJECT_ROOT / "datasets"
RESULTS_DIR   = PROJECT_ROOT / "results"
USE_CASES_DIR = RESULTS_DIR / "use_cases"
AGENTS_DIR    = PROJECT_ROOT / "src" / "agt"

FAMILIES = ("structural", "dynamic", "functional", "procedural")
MODES    = ("apriori", "aposteriori")

DS_GRAPH = "http://dataset/"
NR_GRAPH = "http://noria/"
# Graphs created by Virtuoso itself; everything else is a user graph.
SYSTEM_GRAPH_PREFIXES = ("http://www.openlinksw.com/", "http://www.w3.org/", "urn:activitystreams-owl:map")

LLM_BASELINE_NOTE = "résultats GPU Mistral-7B du 24/04, non relancés"


# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

def parse_args(argv=None) -> argparse.Namespace:
    env = os.environ.get
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("selectors", nargs="*", help="DSxx or DSxx:mode (default: all pairs)")
    p.add_argument("--sparql-url", default=env("MASYN_SPARQL_URL", "http://localhost:8890/sparql"))
    p.add_argument("--crud-url", default=env("MASYN_CRUD_URL", "http://localhost:8890/sparql-graph-crud-auth"))
    p.add_argument("--user", default=env("MASYN_VIRTUOSO_USER", "dba"))
    p.add_argument("--password", default=env("MASYN_VIRTUOSO_PASSWORD", "dba"))
    p.add_argument("--container", default=env("MASYN_VIRTUOSO_CONTAINER", "openlinkvirtuoso"))
    p.add_argument("--noria-dumps", type=Path, default=Path(env(
        "MASYN_NORIA_DUMPS",
        "C:/Program Files/OpenLink Software/Virtuoso OpenSource 7.2/database/dumps")))
    p.add_argument("--python", default=env("MASYN_PYTHON", sys.executable))
    p.add_argument("--eval-results", type=Path, default=PROJECT_ROOT / "eval_results.json",
                   help="reference triple counts (field 'triples')")
    p.add_argument("--ablation-results", type=Path, default=PROJECT_ROOT / "llm_ablation_results.json")
    p.add_argument("--l1-timeout", type=float, default=60.0)
    p.add_argument("--l2-timeout", type=float, default=60.0)
    p.add_argument("--l3-timeout", type=float, default=300.0)
    p.add_argument("--skip-l3", action="store_true")
    p.add_argument("--no-restore-noria", action="store_true",
                   help="leave the last dataset loaded instead of restoring noria")
    return p.parse_args(argv)


# ─────────────────────────────────────────────────────────────────────────────
# GENERIC HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def safe_rmtree(path: Path, allowed_root: Path) -> None:
    """rmtree restricted to a sub-path of allowed_root."""
    path = path.resolve()
    if path == allowed_root.resolve() or allowed_root.resolve() not in path.parents:
        raise RuntimeError(f"refusing to delete {path} (outside {allowed_root})")
    if path.exists():
        shutil.rmtree(path)


def tail(text: str, n: int = 1500) -> str:
    text = text or ""
    return text if len(text) <= n else "…" + text[-n:]


# ─────────────────────────────────────────────────────────────────────────────
# CATALOGUE
# ─────────────────────────────────────────────────────────────────────────────

def dataset_dirs() -> list[Path]:
    return sorted(d for d in DATASETS_DIR.iterdir() if d.is_dir() and (d / "manifest.json").exists())


def manifest_modes(ds_dir: Path) -> list[str]:
    mode = read_json(ds_dir / "manifest.json", {}).get("mode", "both")
    return list(MODES) if mode == "both" else [mode]


def select_pairs(selectors: list[str]) -> list[tuple[Path, str]]:
    pairs = [(d, m) for d in dataset_dirs() for m in manifest_modes(d)]
    if not selectors:
        return pairs
    chosen = []
    for d, m in pairs:
        for s in selectors:
            ds_sel, _, mode_sel = s.partition(":")
            if d.name.startswith(ds_sel) and (not mode_sel or mode_sel == m):
                chosen.append((d, m))
                break
    return chosen


# ─────────────────────────────────────────────────────────────────────────────
# VIRTUOSO (Docker container, HTTP only)
# ─────────────────────────────────────────────────────────────────────────────

class Virtuoso:
    def __init__(self, args: argparse.Namespace):
        self.sparql_url = args.sparql_url
        self.crud_url = args.crud_url
        self.auth = HTTPDigestAuth(args.user, args.password)
        self.container = args.container

    def check_container(self) -> None:
        r = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", self.container],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0 or r.stdout.strip() != "true":
            raise SystemExit(f"Docker container '{self.container}' is not running — start it first "
                             f"(the Windows service Virtuoso_vos must NOT be used).")
        if os.name == "nt":
            s = subprocess.run(["sc", "query", "Virtuoso_vos"], capture_output=True, text=True)
            if "RUNNING" in s.stdout:
                raise SystemExit("Windows service Virtuoso_vos is RUNNING: it would compete with the "
                                 "container on ports 8890/1111. Stop it before running this script.")

    def select(self, query: str) -> list[dict]:
        r = requests.get(self.sparql_url, params={"query": query,
                         "format": "application/sparql-results+json"}, timeout=60)
        r.raise_for_status()
        return r.json()["results"]["bindings"]

    def graph_counts(self) -> dict[str, int]:
        rows = self.select("SELECT ?g (COUNT(*) AS ?n) WHERE { GRAPH ?g { ?s ?p ?o } } GROUP BY ?g")
        return {b["g"]["value"]: int(b["n"]["value"]) for b in rows}

    def user_graph_counts(self) -> dict[str, int]:
        return {g: n for g, n in self.graph_counts().items() if not g.startswith(SYSTEM_GRAPH_PREFIXES)}

    def clear_user_graphs(self) -> None:
        for g in self.user_graph_counts():
            r = requests.delete(self.crud_url, params={"graph": g}, auth=self.auth, timeout=120)
            if r.status_code not in (200, 201, 204, 404):
                raise RuntimeError(f"DELETE graph <{g}> failed: HTTP {r.status_code} {r.text[:200]}")
        left = self.user_graph_counts()
        if left:
            raise RuntimeError(f"user graphs still present after clearing: {left}")

    def load_ttl(self, ttl: Path, graph: str, replace: bool = True) -> None:
        fn = requests.put if replace else requests.post
        r = fn(self.crud_url, params={"graph": graph}, data=ttl.read_bytes(),
               headers={"Content-Type": "text/turtle"}, auth=self.auth, timeout=300)
        if r.status_code not in (200, 201, 204):
            raise RuntimeError(f"loading {ttl.name} into <{graph}> failed: HTTP {r.status_code} {r.text[:200]}")

    def restore_noria(self, dumps: Path) -> dict:
        self.clear_user_graphs()
        files = sorted(dumps.glob("*.ttl"))
        for i, ttl in enumerate(files):
            self.load_ttl(ttl, NR_GRAPH, replace=(i == 0))
        return {"files": [f.name for f in files], "user_graphs": self.user_graph_counts()}


# ─────────────────────────────────────────────────────────────────────────────
# AGENTS
# ─────────────────────────────────────────────────────────────────────────────

def l1_scripts(mode: str) -> list[Path]:
    return sorted(p for fam in FAMILIES for p in (AGENTS_DIR / fam / mode).glob("*.py"))


def l2_scripts(mode: str) -> list[Path]:
    return sorted((AGENTS_DIR / "level2" / mode).glob("*.py"))


def live_dirs(mode: str) -> list[Path]:
    return [RESULTS_DIR / fam / mode for fam in FAMILIES] + [RESULTS_DIR / "level2" / mode]


def snapshot(dirs: list[Path]) -> dict[Path, int]:
    snap = {}
    for d in dirs:
        if d.exists():
            for f in d.glob("*.json"):
                snap[f] = f.stat().st_mtime_ns
    return snap


def run_script(python: str, script: Path, timeout: float, watch: list[Path]) -> tuple[dict, str]:
    before = snapshot(watch)
    t0 = time.perf_counter()
    rec = {"script": script.relative_to(PROJECT_ROOT).as_posix()}
    out = ""
    try:
        r = subprocess.run([python, str(script)], cwd=PROJECT_ROOT, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        rec["returncode"] = r.returncode
        rec["timed_out"] = False
        out = (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired as e:
        rec["returncode"] = None
        rec["timed_out"] = True
        out = (e.stdout or b"").decode("utf-8", "replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
    rec["duration_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    after = snapshot(watch)
    produced = sorted(f for f, m in after.items() if before.get(f) != m)
    rec["outputs"] = [f.relative_to(RESULTS_DIR).as_posix() for f in produced]
    ok = rec["returncode"] == 0 and len(produced) == 1 and read_json(produced[0]) is not None
    rec["status"] = "ok" if ok else ("timeout" if rec["timed_out"] else "failed")
    if not ok and rec["returncode"] == 0:
        rec["error"] = f"expected exactly one readable JSON output, got {len(produced)}"
    return rec, out


# ─────────────────────────────────────────────────────────────────────────────
# METRICS — computed only from the archived folder + dataset ground truth
# ─────────────────────────────────────────────────────────────────────────────

def prf(tp: int, fp: int, fn: int) -> dict:
    """Convention (same as evaluate_datasets.py): P = 1 if TP+FP = 0,
    R = 1 if TP+FN = 0, F1 = 0 if P+R = 0."""
    p = tp / (tp + fp) if (tp + fp) else 1.0
    r = tp / (tp + fn) if (tp + fn) else 1.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3)}


def l2_priority(result: dict) -> tuple[int, int]:
    diags = result.get("diagnoses") or []
    pri = max((d.get("priority_score", 0) or 0 for d in diags), default=-1)
    rel = max((d.get("reliability_score", 0) or 0 for d in diags), default=-1)
    return pri, rel


def compute_metrics(pair_dir: Path, ds_dir: Path, mode: str) -> dict:
    ctx = read_json(pair_dir / "run_context.json", {})
    manifest = read_json(ds_dir / "manifest.json", {})
    exp_l1 = (read_json(ds_dir / "expected_level1.json", {}) or {}).get(mode, {})
    exp_l2 = (read_json(ds_dir / "expected_level2.json", {}) or {}).get(mode, {})

    # ── L1: detectors whose archived JSON is non-empty ───────────────────────
    expected_nonempty = {f"{fam}/{a}" for fam, agents in exp_l1.items() for a, v in agents.items() if v}
    actual_nonempty, l1_counts = set(), {}
    for rec in ctx.get("level1", []):
        fam = Path(rec["script"]).parts[-3]
        name = f"{fam}/{Path(rec['script']).stem}"
        arch = rec.get("archived_output")
        data = read_json(pair_dir / arch, None) if arch else None
        n = len(data) if isinstance(data, list) else 0
        l1_counts[name] = n
        if n > 0:
            actual_nonempty.add(name)
    hit, missed, extra = (expected_nonempty & actual_nonempty, expected_nonempty - actual_nonempty,
                          actual_nonempty - expected_nonempty)
    l1 = {"expected_nonempty": sorted(expected_nonempty), "actual_nonempty": sorted(actual_nonempty),
          "hit": sorted(hit), "missed": sorted(missed), "extra": sorted(extra),
          "tp": len(hit), "fp": len(extra), "fn": len(missed),
          **prf(len(hit), len(extra), len(missed)), "bindings_per_detector": l1_counts}

    # ── L2 ───────────────────────────────────────────────────────────────────
    results = {p.stem: read_json(p, {}) for p in sorted((pair_dir / "level2").glob("*.json"))}
    triggered = [a for a, r in results.items() if r.get("activation_status") == "triggered"]
    expected = sorted(a for a, v in exp_l2.items() if v)
    detail = {}
    for a in sorted(set(results) | set(exp_l2)):
        t, e = a in triggered, a in expected
        detail[a] = "TP" if t and e else "FP" if t else "FN" if e else "TN"
    tp = sum(v == "TP" for v in detail.values())
    fp = sum(v == "FP" for v in detail.values())
    fn = sum(v == "FN" for v in detail.values())

    ranking = sorted(triggered, key=lambda a: (-l2_priority(results[a])[0], -l2_priority(results[a])[1], a))
    ranked = [{"rank": i + 1, "diagnoser": a, "priority_score": l2_priority(results[a])[0],
               "anchor": ((results[a].get("diagnoses") or [{}])[0]).get("target_id"),
               "expected": a in expected} for i, a in enumerate(ranking)]
    expected_rank = {a: (ranking.index(a) + 1 if a in ranking else None) for a in expected}
    first = next((i + 1 for i, a in enumerate(ranking) if a in expected), None)
    order = [x.split("/")[-1] for x in manifest.get("ranking_expectation", []) if x.startswith(mode + "/")]
    l2 = {"expected": expected, "triggered": sorted(triggered), "detail": detail,
          "tp": tp, "fp": fp, "fn": fn, **prf(tp, fp, fn),
          "ranking_by_priority": ranked, "rank_of_expected": expected_rank,
          "top1": ranking[0] if ranking else None,
          "top1_in_expected": bool(ranking) and ranking[0] in expected,
          "reciprocal_rank": round(1 / first, 3) if first else 0.0,
          "manifest_ranking_expectation": order or None,
          "top1_matches_manifest_order": (ranking[0] == order[0]) if (ranking and order) else None}
    return {"dataset_id": ds_dir.name, "mode": mode,
            "conventions": "P=1 if TP+FP=0; R=1 if TP+FN=0; F1=0 if P+R=0. "
                           "L2 ranking = triggered diagnosers sorted by max priority_score "
                           "(tie: reliability, name). L1 = detectors with a non-empty JSON.",
            "level1": l1, "level2": l2}


# ─────────────────────────────────────────────────────────────────────────────
# ONE PAIR
# ─────────────────────────────────────────────────────────────────────────────

def run_pair(ds_dir: Path, mode: str, args, vt: Virtuoso, ref_triples: dict, ablation: list, code_info: dict) -> dict:
    ds = ds_dir.name
    pair_dir = USE_CASES_DIR / ds / mode
    safe_rmtree(pair_dir, USE_CASES_DIR)
    pair_dir.mkdir(parents=True)
    log_lines: list[str] = []

    # Per-DS context files, so each folder reads on its own
    for name in ("README.md", "expected_level2.json"):
        if (ds_dir / name).exists():
            shutil.copy2(ds_dir / name, USE_CASES_DIR / ds / name)

    ctx = {"dataset_id": ds, "mode": mode, "started_at": now_iso(), **code_info,
           "python": args.python, "sparql_url": args.sparql_url, "virtuoso_container": args.container,
           "status": "running"}
    t_start = time.perf_counter()

    def finish(status: str) -> dict:
        ctx["status"] = status
        ctx["finished_at"] = now_iso()
        ctx.setdefault("durations_ms", {})["wall_total"] = round((time.perf_counter() - t_start) * 1000, 1)
        write_json(pair_dir / "run_context.json", ctx)
        (pair_dir / "run_log.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
        return ctx

    # a. Virtuoso: drop every user graph, load the dataset, check the count
    t0 = time.perf_counter()
    try:
        vt.clear_user_graphs()
        vt.load_ttl(ds_dir / "dataset.ttl", DS_GRAPH, replace=True)
        graphs = vt.user_graph_counts()
    except Exception as e:
        ctx["error"] = f"virtuoso: {e}"
        return finish("invalid_load")
    ctx["durations_ms"] = {"load": round((time.perf_counter() - t0) * 1000, 1)}
    loaded = graphs.get(DS_GRAPH, 0)
    # A manifest "triples" field (set when a dataset.ttl was corrected) overrides eval_results.json
    manifest_triples = read_json(ds_dir / "manifest.json", {}).get("triples")
    expected = manifest_triples if manifest_triples is not None else ref_triples.get(ds)
    ctx["triples"] = {"expected": expected,
                      "expected_source": "manifest.json" if manifest_triples is not None else "eval_results.json",
                      "expected_eval_results": ref_triples.get(ds), "loaded_dataset_graph": loaded,
                      "user_graphs": graphs}
    if expected is None or loaded != expected or sum(graphs.values()) != loaded:
        ctx["error"] = "triple count mismatch (or other user graph present)"
        return finish("invalid_triples")

    # b. purge the live result folders of this mode
    for d in live_dirs(mode):
        safe_rmtree(d, RESULTS_DIR)
        d.mkdir(parents=True, exist_ok=True)

    watch = live_dirs(mode)

    # c. L1
    ctx["level1"] = []
    t0 = time.perf_counter()
    for s in l1_scripts(mode):
        rec, out = run_script(args.python, s, args.l1_timeout, watch)
        ctx["level1"].append(rec)
        log_lines += [f"── {rec['script']}  [{rec['status']}] rc={rec['returncode']} {rec['duration_ms']} ms",
                      tail(out).rstrip()]
    ctx["durations_ms"]["l1"] = round((time.perf_counter() - t0) * 1000, 1)
    l1_ok = all(r["status"] == "ok" for r in ctx["level1"])

    # d. L2 (only if every L1 succeeded)
    ctx["level2"] = []
    if l1_ok:
        t0 = time.perf_counter()
        for s in l2_scripts(mode):
            rec, out = run_script(args.python, s, args.l2_timeout, watch)
            ctx["level2"].append(rec)
            log_lines += [f"── {rec['script']}  [{rec['status']}] rc={rec['returncode']} {rec['duration_ms']} ms",
                          tail(out).rstrip()]
        ctx["durations_ms"]["l2"] = round((time.perf_counter() - t0) * 1000, 1)
        ctx["durations_ms"]["total_l1_l2"] = round(ctx["durations_ms"]["l1"] + ctx["durations_ms"]["l2"], 1)
    l2_ok = l1_ok and all(r["status"] == "ok" for r in ctx["level2"])

    # e. archive
    for rec in ctx["level1"]:
        for rel in rec["outputs"]:
            src = RESULTS_DIR / rel
            dst = pair_dir / "level1" / Path(rel).parts[0] / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            rec["archived_output"] = dst.relative_to(pair_dir).as_posix()
    for rec in ctx["level2"]:
        for rel in rec["outputs"]:
            src = RESULTS_DIR / rel
            dst = pair_dir / "level2" / src.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            rec["archived_output"] = dst.relative_to(pair_dir).as_posix()

    # LLM baselines from the existing GPU ablation (not re-run)
    entries = [e for e in ablation if e.get("dataset_id") == ds and e.get("mode") == mode]
    write_json(pair_dir / "llm_baselines.json", {
        "note": LLM_BASELINE_NOTE, "source": "llm_ablation_results.json (origin/paul)",
        "model": entries[0].get("model") if entries else None, "entries": entries})

    if not l1_ok:
        finish("invalid_l1")
        return ctx
    if not l2_ok:
        finish("invalid_l2")
        return ctx

    # f. metrics (from the archived folder only)
    write_json(pair_dir / "run_context.json", ctx)
    write_json(pair_dir / "metrics.json", compute_metrics(pair_dir, ds_dir, mode))

    # g. L3 on the archived folder
    if args.skip_l3:
        ctx["l3"] = {"status": "skipped"}
    else:
        t0 = time.perf_counter()
        cmd = [args.python, str(PROJECT_ROOT / "diagnosis_llm.py"), "--results-dir", str(pair_dir),
               "--mode", mode, "--out-dir", str(pair_dir)]
        try:
            r = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=args.l3_timeout,
                               env={**os.environ, "PYTHONIOENCODING": "utf-8"})
            rc, out, to = r.returncode, (r.stdout or "") + (r.stderr or ""), False
        except subprocess.TimeoutExpired:
            rc, out, to = None, "", True
        ctx["l3"] = {"status": "ok" if rc == 0 and (pair_dir / "l3_narrative.txt").exists() else "failed",
                     "model": "llama3.2:3b", "returncode": rc, "timed_out": to,
                     "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
                     "prompt_saved": (pair_dir / "l3_prompt.txt").exists()}
        if ctx["l3"]["status"] != "ok":
            ctx["l3"]["output_tail"] = tail(out, 800)
        log_lines += ["── L3 diagnosis_llm.py", tail(out).rstrip()]
    return finish("ok")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    args = parse_args(argv)
    vt = Virtuoso(args)
    vt.check_container()

    pairs = select_pairs(args.selectors)
    if not pairs:
        print("No (dataset, mode) pair matches", args.selectors)
        return 1

    ref = read_json(args.eval_results, []) or []
    ref_triples = {r["dataset_id"]: r.get("triples") for r in ref}
    ablation = (read_json(args.ablation_results, {}) or {}).get("results", [])

    agents_vs_paul = subprocess.run(["git", "diff", "--quiet", "origin/paul", "--",
                                     ":(glob)src/agt/**/*.py"], cwd=PROJECT_ROOT).returncode == 0
    code_info = {
        "git_head": git("rev-parse", "HEAD"),
        "git_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "git_dirty_files": len([l for l in git("status", "--porcelain").splitlines() if l.strip()]),
        "agents_py_identical_to_origin_paul": agents_vs_paul,
        "origin_paul": git("rev-parse", "origin/paul"),
        "sha256": {"run_use_cases.py": sha256(Path(__file__)),
                   "diagnosis_llm.py": sha256(PROJECT_ROOT / "diagnosis_llm.py")},
    }
    if not agents_vs_paul:
        print("WARNING: src/agt/**/*.py differs from origin/paul")

    print("=" * 72)
    print(f"  USE-CASE RUNS  ({len(pairs)} pairs)  →  {USE_CASES_DIR}")
    print("=" * 72)
    rc = 0
    try:
        for ds_dir, mode in pairs:
            print(f"  {ds_dir.name:<52} {mode:<12}", end="", flush=True)
            try:
                ctx = run_pair(ds_dir, mode, args, vt, ref_triples, ablation, code_info)
            except Exception as e:
                print(f" ERROR {type(e).__name__}: {e}")
                rc = 1
                continue
            d = ctx.get("durations_ms", {})
            l3 = ctx.get("l3", {}).get("status", "-")
            print(f" {ctx['status']:<15} L1+L2={d.get('total_l1_l2', '-')} ms  L3={l3}")
            if ctx["status"] != "ok":
                rc = 1
    finally:
        if not args.no_restore_noria:
            print("\n  Restoring noria into Virtuoso...", end="", flush=True)
            try:
                info = vt.restore_noria(args.noria_dumps)
                print(f" {info['user_graphs']}")
            except Exception as e:
                print(f" FAILED: {e}")
                rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
