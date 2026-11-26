"""
summarize_use_cases.py  —  Build results/use_cases/SUMMARY.md and summary.json.

Every figure is recomputed from the archived folders
results/use_cases/<DS>/<mode>/ (level1/, level2/, run_context.json) and the
dataset ground truth (datasets/<DS>/expected_level*.json, manifest.json).
Nothing is taken from the variables of run_use_cases.py. The metrics.json
written by the pilot is only used as a consistency check.

Reference values come from eval_results.json on origin/paul (git show).

Usage:
    python -X utf8 summarize_use_cases.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from run_use_cases import (DATASETS_DIR, PROJECT_ROOT, USE_CASES_DIR, compute_metrics,
                           manifest_modes, prf, read_json, dataset_dirs)

MULTI_DIAG = ("DS10", "DS18", "DS23")
ROBUSTNESS = ("DS19", "DS20", "DS21", "DS22")
SCALABILITY = ("DS25", "DS26", "DS27")

# Reported in rapport.txt (tables 17-20) — origin/paul / paul-wip version.
RAPPORT = {
    "table17": {"aposteriori": (0.825, 0.808, 0.815), "apriori": (0.177, 0.740, 0.196),
                "global": (0.394, 0.542, 0.456)},
    "table18": {"top1": 1.000, "mrr": 0.833},
    "table19": {"DS19": 1.00, "DS20": 1.00, "DS21": 1.00, "DS22": 1.00},
    "table20": {"DS25": (170, 4505, 254, 4759), "DS26": (258, 4366, 242, 4608),
                "DS27": (352, 5823, 361, 6434)},
}


def fr(x, nd=3) -> str:
    if x is None:
        return "—"
    if isinstance(x, (int,)) and not isinstance(x, bool):
        return f"{x:,}".replace(",", " ")
    return f"{x:.{nd}f}".replace(".", ",")


def short(a: str) -> str:
    return a.replace("_diagnoser", "")


def git_show_json(ref_path: str):
    r = subprocess.run(["git", "show", ref_path], cwd=PROJECT_ROOT, capture_output=True)
    return json.loads(r.stdout.decode("utf-8")) if r.returncode == 0 else None


def aggregate(rows: list[dict]) -> dict:
    """micro / macro / macro restricted to pairs with >= 1 expected diagnosis."""
    out = {"n": len(rows)}
    if not rows:
        return out
    tp = sum(r["tp"] for r in rows); fp = sum(r["fp"] for r in rows); fn = sum(r["fn"] for r in rows)
    out["micro"] = {"tp": tp, "fp": fp, "fn": fn, **prf(tp, fp, fn)}
    mean = lambda rs, k: round(sum(r[k] for r in rs) / len(rs), 3)
    out["macro"] = {k: mean(rows, k) for k in ("precision", "recall", "f1")}
    rx = [r for r in rows if r["tp"] + r["fn"] > 0]
    out["macro_expected_only"] = ({"n": len(rx), **{k: mean(rx, k) for k in ("precision", "recall", "f1")}}
                                  if rx else {"n": 0})
    return out


def ref_rows() -> list[dict]:
    data = git_show_json("origin/paul:eval_results.json") or []
    rows = []
    for r in data:
        for mode, m in r.get("modes", {}).items():
            lm = m["l2_metrics"]
            rows.append({"dataset_id": r["dataset_id"], "mode": mode, "triples": r.get("triples"),
                         "tp": lm["tp"], "fp": lm["fp"], "fn": lm["fn"],
                         "precision": lm["precision_at_l2"], "recall": lm["recall_at_l2"], "f1": lm["f1_at_l2"],
                         "triggered": sorted(m.get("l2_triggered", []))})
    return rows


def main() -> int:
    rows, consistency = [], []
    for ds_dir in dataset_dirs():
        for mode in manifest_modes(ds_dir):
            pair = USE_CASES_DIR / ds_dir.name / mode
            ctx = read_json(pair / "run_context.json", {}) or {}
            row = {"dataset_id": ds_dir.name, "ds": ds_dir.name[:4], "mode": mode,
                   "status": ctx.get("status", "missing"),
                   "l3": (ctx.get("l3") or {}).get("status", "—"),
                   "triples": (ctx.get("triples") or {}).get("loaded_dataset_graph"),
                   "durations_ms": ctx.get("durations_ms", {}),
                   "l1_scripts": len(ctx.get("level1", [])), "l2_scripts": len(ctx.get("level2", [])),
                   "l1_script_ms": [r["duration_ms"] for r in ctx.get("level1", [])],
                   "l2_script_ms": [r["duration_ms"] for r in ctx.get("level2", [])]}
            if row["status"] == "ok":
                m = compute_metrics(pair, ds_dir, mode)
                l2, l1 = m["level2"], m["level1"]
                row.update({k: l2[k] for k in ("tp", "fp", "fn", "precision", "recall", "f1")})
                row.update({"expected": l2["expected"], "triggered": l2["triggered"],
                            "ranking": l2["ranking_by_priority"], "rank_of_expected": l2["rank_of_expected"],
                            "top1": l2["top1"], "top1_in_expected": l2["top1_in_expected"],
                            "reciprocal_rank": l2["reciprocal_rank"],
                            "manifest_order": l2["manifest_ranking_expectation"],
                            "top1_matches_manifest_order": l2["top1_matches_manifest_order"],
                            "l1": {k: l1[k] for k in ("tp", "fp", "fn", "precision", "recall", "hit", "missed", "extra")}})
                pilot = read_json(pair / "metrics.json", {})
                if pilot != m:
                    consistency.append(f"{ds_dir.name}/{mode}: metrics.json differs from recomputation")
            rows.append(row)

    ok = [r for r in rows if r["status"] == "ok"]
    no_llm = sum(1 for r in ok if (USE_CASES_DIR / r["dataset_id"] / r["mode"] / "l3_prompt.txt").exists()
                 and (USE_CASES_DIR / r["dataset_id"] / r["mode"] / "l3_prompt.txt")
                 .read_text(encoding="utf-8").startswith("(no prompt"))
    agg ={sel: aggregate([r for r in ok if sel == "global" or r["mode"] == sel])
           for sel in ("apriori", "aposteriori", "global")}
    l1_agg = {}
    for sel in ("apriori", "aposteriori", "global"):
        rs = [r for r in ok if sel == "global" or r["mode"] == sel]
        tp = sum(r["l1"]["tp"] for r in rs); fp = sum(r["l1"]["fp"] for r in rs); fn = sum(r["l1"]["fn"] for r in rs)
        l1_agg[sel] = {"n": len(rs), "tp": tp, "fp": fp, "fn": fn, **prf(tp, fp, fn)}

    ref = ref_rows()
    ref_by = {(r["dataset_id"], r["mode"]): r for r in ref}
    ref_agg = {sel: aggregate([r for r in ref if sel == "global" or r["mode"] == sel])
               for sel in ("apriori", "aposteriori", "global")}
    # Datasets whose dataset.ttl was corrected (manifest "triples" field): the eval_results.json
    # reference was computed on a truncated graph, so these pairs are not comparable with it.
    corrected = {d.name: read_json(d / "manifest.json", {}).get("triples") for d in dataset_dirs()
                 if read_json(d / "manifest.json", {}).get("triples") is not None}
    comparable = [r for r in ok if r["dataset_id"] not in corrected]
    noncomp = [r for r in ok if r["dataset_id"] in corrected]
    comp_keys = {(r["dataset_id"], r["mode"]) for r in comparable}
    ref_same = [r for r in ref if (r["dataset_id"], r["mode"]) in comp_keys]
    ref_agg_same = {sel: aggregate([r for r in ref_same if sel == "global" or r["mode"] == sel])
                    for sel in ("apriori", "aposteriori", "global")}
    agg_comp = {sel: aggregate([r for r in comparable if sel == "global" or r["mode"] == sel])
                for sel in ("apriori", "aposteriori", "global")}
    invalid = [r for r in rows if r["status"] != "ok"]

    from collections import Counter
    l1_missed = Counter((r["mode"], x) for r in ok for x in r["l1"]["missed"])
    l1_extra = Counter((r["mode"], x) for r in ok for x in r["l1"]["extra"])

    # ── per-pair comparison with eval_results.json ───────────────────────────
    def pair_diff(r):
        e = ref_by.get((r["dataset_id"], r["mode"]))
        if not e:
            return None, "absent d'eval_results.json"
        what = []
        if sorted(r["triggered"]) != e["triggered"]:
            what.append(f"déclenchés {[short(x) for x in e['triggered']]} → {[short(x) for x in r['triggered']]}")
        if (r["tp"], r["fp"], r["fn"]) != (e["tp"], e["fp"], e["fn"]):
            what.append(f"TP/FP/FN {e['tp']}/{e['fp']}/{e['fn']} → {r['tp']}/{r['fp']}/{r['fn']}")
        if r["triples"] != e["triples"]:
            what.append(f"triplets {e['triples']} → {r['triples']}")
        return e, "; ".join(what)

    diffs, noncomp_diffs = [], []
    for r in comparable:
        e, d = pair_diff(r)
        if d:
            diffs.append((r, e, d))
    for r in noncomp:
        e, d = pair_diff(r)
        noncomp_diffs.append((r, e, d or "aucun écart"))

    # ── ranking ──────────────────────────────────────────────────────────────
    rank_rows = [r for r in ok if r["ds"] in MULTI_DIAG]
    top1 = round(sum(r["top1_in_expected"] for r in rank_rows) / len(rank_rows), 3) if rank_rows else None
    mrr = round(sum(r["reciprocal_rank"] for r in rank_rows) / len(rank_rows), 3) if rank_rows else None
    ds24 = next((r for r in ok if r["ds"] == "DS24" and r["mode"] == "apriori"), None)
    rank4 = rank_rows + ([ds24] if ds24 else [])
    mrr4 = round(sum(r["reciprocal_rank"] for r in rank4) / len(rank4), 3) if rank4 else None
    top1_4 = round(sum(r["top1_in_expected"] for r in rank4) / len(rank4), 3) if rank4 else None

    summary = {"generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
               "source": "results/use_cases/<DS>/<mode>/ (recomputed), datasets/*/expected_level*.json",
               "conventions": {
                   "prf": "P = TP/(TP+FP), = 1 if TP+FP = 0; R = TP/(TP+FN), = 1 if TP+FN = 0; "
                          "F1 = 2PR/(P+R), = 0 if P+R = 0 (same as evaluate_datasets.py)",
                   "micro": "TP/FP/FN summed over pairs, then P/R/F1",
                   "macro": "mean over pairs of per-pair P, R, F1",
                   "macro_expected_only": "macro restricted to pairs with >= 1 expected L2 diagnosis",
                   "ranking": "triggered diagnosers sorted by max priority_score (tie: reliability, name); "
                              "Top-1 = first is an expected diagnoser; RR = 1/rank of the first expected "
                              "diagnoser (0 if none); MRR = mean RR",
                   "l1": "detector counted as fired iff its archived JSON is a non-empty list"},
               "pairs": rows, "aggregates_l2": agg, "aggregates_l1": l1_agg,
               "reference_eval_results": {"aggregates_l2": ref_agg,
                                          "aggregates_l2_comparable_pairs": ref_agg_same,
                                          "this_run_aggregates_l2_comparable_pairs": agg_comp,
                                          "non_comparable_pairs": [
                                              {"pair": f"{r['dataset_id']}/{r['mode']}",
                                               "reason": "dataset.ttl corrected; reference computed on a truncated graph",
                                               "reference_triples": (ref_by.get((r["dataset_id"], r["mode"])) or {}).get("triples"),
                                               "corrected_triples": corrected[r["dataset_id"]]} for r in noncomp]},
               "invalid_pairs": [{"pair": f"{r['dataset_id']}/{r['mode']}", "status": r["status"]} for r in invalid],
               "l1_missed": {f"{m}/{a}": n for (m, a), n in l1_missed.most_common()},
               "l1_extra": {f"{m}/{a}": n for (m, a), n in l1_extra.most_common()},
               "ranking": {"pairs": [r["dataset_id"] + "/" + r["mode"] for r in rank_rows], "top1": top1, "mrr": mrr,
                           "with_ds24_apriori": {"top1": top1_4, "mrr": mrr4}},
               "diffs_vs_eval_results": [{"pair": f"{r['dataset_id']}/{r['mode']}", "diff": d} for r, e, d in diffs],
               "diffs_non_comparable_pairs": [{"pair": f"{r['dataset_id']}/{r['mode']}", "diff": d}
                                              for r, e, d in noncomp_diffs],
               "consistency_issues": consistency}
    (USE_CASES_DIR / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                                                encoding="utf-8")

    # ── Markdown ─────────────────────────────────────────────────────────────
    L = []
    w = L.append
    ctx0 = read_json(USE_CASES_DIR / ok[0]["dataset_id"] / ok[0]["mode"] / "run_context.json", {}) if ok else {}
    w("# Runs L1 + L2 + L3 sur les 27 use cases (36 couples dataset × mode)\n")
    w(f"Généré le {summary['generated_at']} par `summarize_use_cases.py`. Tous les chiffres sont recalculés "
      "depuis les dossiers `results/use_cases/<DS>/<mode>/` et la ground truth des datasets.\n")
    w(f"- Code : branche `{ctx0.get('git_branch')}`, HEAD `{(ctx0.get('git_head') or '')[:7]}` ; scripts "
      f"`src/agt/**/*.py` identiques à `origin/paul` (`{(ctx0.get('origin_paul') or '')[:7]}`) : "
      f"**{ctx0.get('agents_py_identical_to_origin_paul')}**.")
    w("- Exécution : `run_use_cases.py`, scripts Python appelés directement (sans JaCaMo), en séquentiel ; "
      "Virtuoso = conteneur Docker `openlinkvirtuoso`, tous les graphes utilisateur vidés avant chaque dataset.")
    w(f"- Statuts : {sum(r['status'] == 'ok' for r in rows)}/{len(rows)} runs valides ; "
      f"L3 : {sum(r['l3'] == 'ok' for r in rows)} narrations OK, {sum(r['l3'] == 'failed' for r in rows)} échecs ; "
      f"dont {no_llm} couples sans aucune alerte L1/L2, pour lesquels le LLM n'est pas appelé "
      "(message fixe de `diagnosis_llm.py`).")
    if consistency:
        w(f"- ⚠ Incohérences metrics.json / recalcul : {consistency}")
    w("\n**Conventions.** P = TP/(TP+FP), fixée à **1** si TP+FP = 0 ; R = TP/(TP+FN), fixée à **1** si "
      "TP+FN = 0 ; F1 = 0 si P+R = 0 (convention d'`evaluate_datasets.py`, qui redonne exactement les valeurs "
      "de référence). Un couple sans diagnostic attendu ni déclenché vaut donc P = R = F1 = 1 ; un faux "
      "positif seul donne P = 0, R = 1, F1 = 0. Micro = TP/FP/FN cumulés ; macro = moyenne des P, R, F1 par "
      "couple. L1 : un détecteur compte comme déclenché si son JSON archivé est une liste non vide.\n")

    w("## 1. Les 36 runs\n")
    w("| DS | Mode | Triplets | L2 attendus | L2 déclenchés | TP/FP/FN | F1 | L1+L2 (ms) | Statut | L3 |")
    w("|---|---|---:|---|---|---|---:|---:|---|---|")
    for r in rows:
        if r["status"] == "ok":
            star = " ¹" if r["dataset_id"] in corrected else ""
            w(f"| {r['dataset_id']} | {r['mode']} | {r['triples']}{star} | "
              f"{', '.join(short(x) for x in r['expected']) or '—'} | "
              f"{', '.join(short(x) for x in r['triggered']) or '—'} | {r['tp']}/{r['fp']}/{r['fn']} | "
              f"{fr(r['f1'])} | {fr(int(round(r['durations_ms'].get('total_l1_l2', 0))))} | ok | {r['l3']} |")
        else:
            w(f"| {r['dataset_id']} | {r['mode']} | {r['triples'] or '—'} | — | — | — | — | — | "
              f"**{r['status']}** | {r['l3']} |")
    if corrected:
        w("\n¹ `dataset.ttl` corrigé le 2026-11-26 (`;` orphelin remplacé par `.`) ; nombre de triplets de référence "
          "pris dans `manifest.json` ("
          + ", ".join(f"{k[:4]} : {v}" for k, v in sorted(corrected.items())) + ").")

    w("\n## 2. Agrégats L2\n")
    w("| Périmètre | n | Micro P / R / F1 (TP/FP/FN) | Macro P / R / F1 | Macro, couples avec ≥ 1 attendu (n) |")
    w("|---|---:|---|---|---|")
    for sel in ("apriori", "aposteriori", "global"):
        a = agg[sel]
        if a["n"] == 0:
            continue
        mi, ma, mx = a["micro"], a["macro"], a["macro_expected_only"]
        w(f"| {sel} | {a['n']} | {fr(mi['precision'])} / {fr(mi['recall'])} / {fr(mi['f1'])} "
          f"({mi['tp']}/{mi['fp']}/{mi['fn']}) | {fr(ma['precision'])} / {fr(ma['recall'])} / {fr(ma['f1'])} | "
          + (f"{fr(mx['precision'])} / {fr(mx['recall'])} / {fr(mx['f1'])} ({mx['n']})" if mx["n"] else "—") + " |")
    w("\n**L1 (détecteurs à sortie non vide vs `expected_level1.json`, micro).**\n")
    w("| Périmètre | n | TP / FP / FN | P / R |")
    w("|---|---:|---|---|")
    for sel, a in l1_agg.items():
        w(f"| {sel} | {a['n']} | {a['tp']} / {a['fp']} / {a['fn']} | {fr(a['precision'])} / {fr(a['recall'])} |")
    w("\nDétecteurs attendus mais vides (*missed*) et non attendus mais non vides (*extra*), en nombre de couples :\n")
    w("| Mode / détecteur | missed | extra |")
    w("|---|---:|---:|")
    for k in sorted(set(l1_missed) | set(l1_extra), key=lambda k: (-(l1_missed[k] + l1_extra[k]), k)):
        w(f"| {k[0]} / {k[1]} | {l1_missed[k] or ''} | {l1_extra[k] or ''} |")

    w("\n## 3. Classement (DS10, DS18, DS23)\n")
    w("| Couple | Classement par priority_score (priorité) | Rang des attendus | Top-1 ∈ attendus | RR |")
    w("|---|---|---|---|---:|")
    for r in rank_rows + ([ds24] if ds24 else []):
        rk = ", ".join(f"{x['rank']}. {short(x['diagnoser'])} ({x['priority_score']})" for x in r["ranking"]) or "—"
        ex = ", ".join(f"{short(a)}: {v if v else '∅'}" for a, v in r["rank_of_expected"].items())
        tag = " *(hors périmètre demandé, dataset corrigé)*" if r["ds"] == "DS24" else ""
        w(f"| {r['ds']} {r['mode']}{tag} | {rk} | {ex} | {'oui' if r['top1_in_expected'] else 'non'} | "
          f"{fr(r['reciprocal_rank'])} |")
    w(f"\n**DS10 + DS18 + DS23 : Top-1 = {fr(top1)}, MRR = {fr(mrr)}** (n = {len(rank_rows)}). "
      + (f"Avec DS24 apriori (4 couples à ≥ 2 attendus, périmètre de `kpi_analysis.py`) : "
         f"Top-1 = {fr(top1_4)}, MRR = {fr(mrr4)}." if ds24 else
         "DS24 apriori (4ᵉ couple à ≥ 2 attendus dans `kpi_analysis.py`) n'a pas de run valide : non inclus."))
    ds23 = next((r for r in rank_rows if r["ds"] == "DS23"), None)
    if ds23 and ds23.get("manifest_order"):
        got = [x["diagnoser"] for x in ds23["ranking"] if x["expected"]]
        w(f"\nDS23, ordre attendu par le manifest : {' > '.join(short(x) for x in ds23['manifest_order'])} ; "
          f"ordre obtenu : {' > '.join(short(x) for x in got) or '—'} ; "
          f"Top-1 conforme au manifest : **{'oui' if ds23['top1_matches_manifest_order'] else 'non'}**.")

    w("\n## 4. Robustesse (DS19–DS22)\n")
    w("| Couple | Attendus | Déclenchés | TP/FP/FN | F1 | Rapport (tab. 19) |")
    w("|---|---|---|---|---:|---:|")
    for r in ok:
        if r["ds"] in ROBUSTNESS:
            w(f"| {r['ds']} {r['mode']} | {', '.join(short(x) for x in r['expected']) or '—'} | "
              f"{', '.join(short(x) for x in r['triggered']) or '—'} | {r['tp']}/{r['fp']}/{r['fn']} | "
              f"{fr(r['f1'])} | {fr(RAPPORT['table19'][r['ds']], 2)} |")

    w("\n## 5. Temps d'exécution (DS25–DS27)\n")
    w("| Couple | Triplets | L1 (ms) | L2 (ms) | L1+L2 (ms) | L3 (ms) | ms / script L1 (moy.) | Rapport tab. 20 : L1 / L2 / total (ms) |")
    w("|---|---:|---:|---:|---:|---:|---:|---|")
    for r in ok:
        if r["ds"] in SCALABILITY:
            d = r["durations_ms"]
            rp = RAPPORT["table20"][r["ds"]]
            l3ms = (read_json(USE_CASES_DIR / r["dataset_id"] / r["mode"] / "run_context.json", {}) or {}).get("l3", {}).get("duration_ms")
            per = sum(r["l1_script_ms"]) / len(r["l1_script_ms"]) if r["l1_script_ms"] else None
            w(f"| {r['ds']} {r['mode']} | {r['triples']} | {fr(int(round(d.get('l1', 0))))} | "
              f"{fr(int(round(d.get('l2', 0))))} | {fr(int(round(d.get('total_l1_l2', 0))))} | "
              f"{fr(int(round(l3ms))) if l3ms else '—'} | {fr(int(round(per))) if per else '—'} | "
              f"{fr(rp[1])} / {fr(rp[2])} / {fr(rp[3])} |")

    w("\n## 6. Comparaison avec `eval_results.json` (origin/paul) et avec le rapport\n")
    w("### 6.1 Agrégats\n")
    w(f"« Référence » = recalcul depuis `eval_results.json` (36 couples). « Couples comparables » = les "
      f"{len(comparable)} couples valides de ce run dont le dataset n'a pas été modifié : c'est la seule "
      f"comparaison à périmètre égal. « Ce run ({len(ok)}) » inclut tous les couples valides de ce run.\n")
    if noncomp:
        w("**Couples non comparables avec la référence du 24/04.** "
          + ", ".join(f"{r['dataset_id'][:4]} {r['mode']}" for r in noncomp)
          + " : leur `dataset.ttl` a été corrigé (`;` orphelin remplacé par `.`). La référence d'`eval_results.json` "
          "pour ces couples a été calculée sur des graphes tronqués ("
          + ", ".join(f"{k[:4]} : {(next((e for (d, _), e in ref_by.items() if d == k), {}) or {}).get('triples')} "
                      f"triplets au lieu de {v}" for k, v in sorted(corrected.items()))
          + ") ; elle n'est donc pas comparable. Ces couples sont exclus des colonnes « couples comparables » "
          "et inclus dans la dernière colonne.\n")
    w(f"| Indicateur | Rapport | Référence (36 couples) | Référence, couples comparables ({len(comparable)}) "
      f"| Ce run, couples comparables ({len(comparable)}) | Ce run ({len(ok)}) |")
    w("|---|---|---|---|---|---|")
    def trio(t): return " / ".join(fr(x) for x in t)
    def get(a, kind): return (a[kind]["precision"], a[kind]["recall"], a[kind]["f1"]) if a.get(kind) else None
    lines = [
        ("Apriori macro P/R/F1 (tab. 17)", RAPPORT["table17"]["apriori"], "apriori", "macro"),
        ("Aposteriori macro P/R/F1 (tab. 17)", RAPPORT["table17"]["aposteriori"], "aposteriori", "macro"),
        ("Aposteriori micro P/R/F1", None, "aposteriori", "micro"),
        ("Apriori micro P/R/F1", None, "apriori", "micro"),
        ("Global micro P/R/F1 (tab. 17)", RAPPORT["table17"]["global"], "global", "micro"),
        ("Global macro P/R/F1", None, "global", "macro"),
    ]
    for name, rp, sel, kind in lines:
        cells = [get(ref_agg[sel], kind), get(ref_agg_same[sel], kind), get(agg_comp[sel], kind),
                 get(agg[sel], kind)]
        w(f"| {name} | {trio(rp) if rp else '—'} | " + " | ".join(trio(c) if c else "—" for c in cells) + " |")
    w(f"| Top-1 / MRR (tab. 18) | {fr(RAPPORT['table18']['top1'])} / {fr(RAPPORT['table18']['mrr'])} | — | — | "
      f"{fr(top1)} / {fr(mrr)} (DS10, 18, 23) | {fr(top1)} / {fr(mrr)} (DS10, 18, 23) |")
    if invalid:
        w(f"\nCouples sans run valide ({len(invalid)}) : "
          + ", ".join(f"{r['dataset_id']} {r['mode']} (**{r['status']}**)" for r in invalid) + ".")

    w("\n### 6.2 Écarts couple par couple avec eval_results.json\n")
    if not diffs:
        w("Aucun écart : mêmes diagnoseurs déclenchés, mêmes TP/FP/FN et mêmes nombres de triplets sur les "
          f"{len(comparable)} couples comparables.")
    else:
        w("| Couple | Écart |")
        w("|---|---|")
        for r, e, d in diffs:
            w(f"| {r['dataset_id']} {r['mode']} | {d} |")
    if noncomp_diffs:
        w("\nCouples non comparables (dataset corrigé, référence calculée sur un graphe tronqué), à titre indicatif :\n")
        w("| Couple | Référence 24/04 → ce run |")
        w("|---|---|")
        for r, e, d in noncomp_diffs:
            w(f"| {r['dataset_id']} {r['mode']} | {d} |")
    w("\n### 6.3 Écarts avec le rapport et explications probables\n")
    notes = USE_CASES_DIR / "SUMMARY_notes.md"
    w(notes.read_text(encoding="utf-8").strip() + "\n" if notes.exists()
      else "_(pas de notes : créer results/use_cases/SUMMARY_notes.md)_\n")
    (USE_CASES_DIR / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Wrote {USE_CASES_DIR / 'SUMMARY.md'} and summary.json ({len(ok)}/{len(rows)} valid runs, "
          f"{len(comparable)} comparable, {len(diffs)} diffs vs eval_results, "
          f"{len(consistency)} consistency issues)")
    for r, e, d in noncomp_diffs:
        print(f"  non-comparable {r['dataset_id']}/{r['mode']}: {d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
