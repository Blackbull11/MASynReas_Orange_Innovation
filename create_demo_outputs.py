"""
create_demo_outputs.py  —  Generate realistic mock output files for the soutenance demo.

Simulates a successful run on DS11_single_point_of_failure_basic (aposteriori mode).
The anchor is res_firewall_01 — isolated firewall with no redundancy, linked to incidents.

Run: python create_demo_outputs.py
"""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

# ── helpers ──────────────────────────────────────────────────────────────────

def uri(local):
    return {"type": "uri", "value": f"http://dataset/{local}"}

def lit(val, dtype="string"):
    r = {"type": "literal", "value": str(val)}
    if dtype == "integer":
        r["datatype"] = "http://www.w3.org/2001/XMLSchema#integer"
    elif dtype == "decimal":
        r["datatype"] = "http://www.w3.org/2001/XMLSchema#decimal"
    return r

def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [OK] {path.relative_to(ROOT)}")

def empty(path):
    write(path, [])

def not_triggered(path, agent, mode, reason):
    write(path, {
        "agent": agent,
        "mode": mode,
        "activation_status": "not_triggered",
        "reason": reason,
        "diagnoses": []
    })

# ── L1 structural/aposteriori ────────────────────────────────────────────────

print("\n=== L1 structural/aposteriori ===")

write(RESULTS / "structural/aposteriori/isolated_incident_resource_results.json", [
    {
        "ticket":            uri("ticket_incident_001"),
        "resource":          uri("res_firewall_01"),
        "connectivityDegree": lit(1, "integer")
    }
])

write(RESULTS / "structural/aposteriori/no_redundancy_incident_results.json", [
    {
        "resource":    uri("res_firewall_01"),
        "ticket":      uri("ticket_incident_001"),
        "redundantResource": lit("none")
    }
])

write(RESULTS / "structural/aposteriori/high_impact_resource_results.json", [
    {
        "resource":           uri("res_firewall_01"),
        "downstreamCount":    lit(4, "integer"),
        "affectedService":    uri("service_workforce_portal")
    }
])

write(RESULTS / "structural/aposteriori/incident_on_incomplete_link_results.json", [
    {
        "resource":    uri("res_firewall_01"),
        "link":        uri("link_fw01_core"),
        "ticket":      uri("ticket_incident_001"),
        "missingEnd":  lit("true")
    }
])

write(RESULTS / "structural/aposteriori/child_component_incident_escalation_results.json", [
    {
        "parentResource": uri("res_firewall_01"),
        "childResource":  uri("res_fw01_module_a"),
        "ticket":         uri("ticket_incident_001")
    }
])

empty(RESULTS / "structural/aposteriori/application_mapping_inconsistency_results.json")
empty(RESULTS / "structural/aposteriori/spatial_incident_cluster_results.json")

# ── L1 dynamic/aposteriori ───────────────────────────────────────────────────

print("\n=== L1 dynamic/aposteriori ===")

DYNAMIC_EMPTY = [
    "change_followed_by_incident_results.json",
    "change_overlap_conflict_results.json",
    "critical_event_ticket_escalation_results.json",
    "event_burst_results.json",
    "flapping_state_results.json",
    "incident_propagation_results.json",
    "multi_element_synchronous_incident_results.json",
    "parent_child_event_results.json",
    "reopened_incident_results.json",
    "repeated_similar_event_results.json",
    "silent_degradation_after_change_results.json",
    "stale_incident_results.json",
]
for fname in DYNAMIC_EMPTY:
    empty(RESULTS / f"dynamic/aposteriori/{fname}")

# ── L1 functional/aposteriori ────────────────────────────────────────────────

print("\n=== L1 functional/aposteriori ===")

FUNCTIONAL_EMPTY = [
    "application_incident_without_resource_results.json",
    "cascading_service_failure_results.json",
    "conflicting_application_state_results.json",
    "hidden_service_dependency_results.json",
    "module_level_incident_aggregation_results.json",
    "resource_event_without_service_impact_results.json",
    "service_impacted_by_multiple_resources_results.json",
    "service_with_repeated_incident_results.json",
    "service_without_ticket_escalation_results.json",
]
for fname in FUNCTIONAL_EMPTY:
    empty(RESULTS / f"functional/aposteriori/{fname}")

# ── L1 procedural/aposteriori ────────────────────────────────────────────────

print("\n=== L1 procedural/aposteriori ===")

PROCEDURAL_EMPTY = [
    "change_linked_to_multiple_incidents_results.json",
    "incident_without_ticket_results.json",
    "ticket_without_linked_event_results.json",
]
for fname in PROCEDURAL_EMPTY:
    empty(RESULTS / f"procedural/aposteriori/{fname}")

# ── L2 aposteriori ───────────────────────────────────────────────────────────

print("\n=== L2 aposteriori ===")

write(RESULTS / "level2/aposteriori/single_point_of_failure_diagnoser.json", {
    "agent": "single_point_of_failure_diagnoser",
    "mode": "aposteriori",
    "activation_status": "triggered",
    "reason": "Resource 'res_firewall_01' concentrates structural incident evidence from 4 primary agents.",
    "diagnoses": [
        {
            "diagnosis_id": "L2-P1-1",
            "diagnosis_type": "single_point_of_failure",
            "diagnosis_label": "Single point of failure",
            "target_type": "Resource",
            "target_id": "http://dataset/res_firewall_01",
            "reliability_score": 75,
            "severity_score": 63,
            "priority_score": 70,
            "recommended_action": "Inspect res_firewall_01 for topology isolation, missing failover, and incomplete link declarations. Add a redundant firewall path or a hot-standby unit.",
            "explanation": (
                "Single point of failure is diagnosed for Resource 'res_firewall_01' "
                "because incident resources appear isolated (connectivityDegree=1); "
                "incident resources have no visible redundancy; "
                "incident resources have broad downstream impact (4 dependent services); "
                "incident resources sit on an incomplete network link. "
                "Evidence converges from the structural signal family."
            ),
            "evidence": [
                {
                    "level1_agent": "isolated_incident_resource_detector",
                    "role": "primary",
                    "matched_anchor": "http://dataset/res_firewall_01",
                    "record_count": 1,
                    "family": "structural",
                    "result_file": "results/structural/aposteriori/isolated_incident_resource_results.json"
                },
                {
                    "level1_agent": "no_redundancy_incident_detector",
                    "role": "primary",
                    "matched_anchor": "http://dataset/res_firewall_01",
                    "record_count": 1,
                    "family": "structural",
                    "result_file": "results/structural/aposteriori/no_redundancy_incident_results.json"
                },
                {
                    "level1_agent": "high_impact_resource_detector",
                    "role": "primary",
                    "matched_anchor": "http://dataset/res_firewall_01",
                    "record_count": 1,
                    "family": "structural",
                    "result_file": "results/structural/aposteriori/high_impact_resource_results.json"
                },
                {
                    "level1_agent": "incident_on_incomplete_link_detector",
                    "role": "primary",
                    "matched_anchor": "http://dataset/res_firewall_01",
                    "record_count": 1,
                    "family": "structural",
                    "result_file": "results/structural/aposteriori/incident_on_incomplete_link_results.json"
                },
                {
                    "level1_agent": "child_component_incident_escalation_detector",
                    "role": "supporting",
                    "matched_anchor": "http://dataset/res_firewall_01",
                    "record_count": 1,
                    "family": "structural",
                    "result_file": "results/structural/aposteriori/child_component_incident_escalation_results.json"
                }
            ]
        }
    ]
})

for agent, reason in [
    ("change_induced_incident_diagnoser",     "No change event precedes the incident on res_firewall_01 within the observation window."),
    ("service_cascade_diagnoser",             "Only one service is directly affected; no cascade pattern detected."),
    ("traceability_breakdown_diagnoser",      "ticket_incident_001 is properly linked to a procedure and event chain."),
    ("unstable_component_diagnoser",          "No repeated incident pattern detected on res_firewall_01."),
    ("application_support_failure_diagnoser", "All applications have adequate resource support in the current graph."),
    ("local_infrastructure_cluster_diagnoser","No co-located resource cluster failures detected."),
]:
    not_triggered(RESULTS / f"level2/aposteriori/{agent}.json", agent, "aposteriori", reason)

# ── metrics ──────────────────────────────────────────────────────────────────

print("\n=== metrics ===")

import time
ts = int(time.time() * 1000)

(RESULTS / "metrics").mkdir(parents=True, exist_ok=True)

# runtime_events.jsonl
events = [
    {"event": "mas_started",      "dataset_id": "DS11_single_point_of_failure_basic", "mode": "aposteriori", "epoch_ms": ts - 8200},
]

l1_scripts = [
    ("structural/aposteriori/isolated_incident_resource_detector.py",          "structural", ts-8100, ts-7800),
    ("structural/aposteriori/no_redundancy_incident_detector.py",               "structural", ts-8100, ts-7750),
    ("structural/aposteriori/high_impact_resource_detector.py",                 "structural", ts-8100, ts-7820),
    ("structural/aposteriori/incident_on_incomplete_link_detector.py",          "structural", ts-8100, ts-7840),
    ("structural/aposteriori/child_component_incident_escalation_detector.py",  "structural", ts-8100, ts-7900),
    ("structural/aposteriori/application_mapping_inconsistency_detector.py",    "structural", ts-8100, ts-7780),
    ("structural/aposteriori/spatial_incident_cluster_detector.py",             "structural", ts-8100, ts-7760),
    ("dynamic/aposteriori/change_followed_by_incident_detector.py",             "dynamic",    ts-8100, ts-7810),
    ("dynamic/aposteriori/change_overlap_conflict.py",                          "dynamic",    ts-8100, ts-7770),
    ("dynamic/aposteriori/critical_event_ticket_escalation_detector.py",        "dynamic",    ts-8100, ts-7830),
    ("dynamic/aposteriori/event_burst_detector.py",                             "dynamic",    ts-8100, ts-7790),
    ("dynamic/aposteriori/flapping_state_detector.py",                          "dynamic",    ts-8100, ts-7800),
    ("dynamic/aposteriori/incident_propagation_detector.py",                    "dynamic",    ts-8100, ts-7850),
    ("dynamic/aposteriori/multi_element_synchronous_incident_detector.py",      "dynamic",    ts-8100, ts-7760),
    ("dynamic/aposteriori/parent_child_event_escalation_detector.py",           "dynamic",    ts-8100, ts-7820),
    ("dynamic/aposteriori/reopened_incident_detector.py",                       "dynamic",    ts-8100, ts-7780),
    ("dynamic/aposteriori/repeated_similar_event_detector.py",                  "dynamic",    ts-8100, ts-7800),
    ("dynamic/aposteriori/silent_degradation_after_change_detector.py",         "dynamic",    ts-8100, ts-7840),
    ("dynamic/aposteriori/stale_incident_detector.py",                          "dynamic",    ts-8100, ts-7810),
    ("functional/aposteriori/application_incident_without_resource_detector.py","functional", ts-8100, ts-7760),
    ("functional/aposteriori/cascading_service_failure_detector.py",            "functional", ts-8100, ts-7830),
    ("functional/aposteriori/conflicting_application_state_detector.py",        "functional", ts-8100, ts-7780),
    ("functional/aposteriori/hidden_service_dependency_detector.py",            "functional", ts-8100, ts-7800),
    ("functional/aposteriori/module_level_incident_aggregation_detector.py",    "functional", ts-8100, ts-7850),
    ("functional/aposteriori/resource_event_without_service_impact_detector.py","functional", ts-8100, ts-7770),
    ("functional/aposteriori/service_impacted_by_multiple_resources_detector.py","functional",ts-8100, ts-7820),
    ("functional/aposteriori/service_with_repeated_incident_detector.py",       "functional", ts-8100, ts-7790),
    ("functional/aposteriori/service_without_ticket_escalation_detector.py",    "functional", ts-8100, ts-7810),
    ("procedural/aposteriori/change_linked_to_multiple_incidents_detector.py",  "procedural", ts-8100, ts-7840),
    ("procedural/aposteriori/incident_without_ticket_detector.py",              "procedural", ts-8100, ts-7760),
    ("procedural/aposteriori/ticket_without_linked_event_detector.py",          "procedural", ts-8100, ts-7790),
]

for path, family, start, end in l1_scripts:
    events.append({
        "event": "script_finished",
        "dataset_id": "DS11_single_point_of_failure_basic",
        "mode": "aposteriori",
        "script_path": f"src/agt/{path}",
        "script_name": Path(path).name,
        "catalogue_level": "level1",
        "domain_family": family,
        "phase": "aposteriori",
        "start_epoch_ms": start,
        "end_epoch_ms": end,
        "duration_ms": end - start,
        "status": "success",
        "exit_code": 0,
        "latest_level1_end_epoch_ms": ts - 7750
    })

l2_scripts = [
    ("single_point_of_failure_diagnoser",    ts-7700, ts-7400),
    ("change_induced_incident_diagnoser",    ts-7700, ts-7350),
    ("service_cascade_diagnoser",            ts-7700, ts-7380),
    ("traceability_breakdown_diagnoser",     ts-7700, ts-7360),
    ("unstable_component_diagnoser",         ts-7700, ts-7370),
    ("application_support_failure_diagnoser",ts-7700, ts-7340),
    ("local_infrastructure_cluster_diagnoser",ts-7700,ts-7330),
]

for name, start, end in l2_scripts:
    events.append({
        "event": "script_finished",
        "dataset_id": "DS11_single_point_of_failure_basic",
        "mode": "aposteriori",
        "script_path": f"src/agt/level2/aposteriori/{name}.py",
        "script_name": f"{name}.py",
        "catalogue_level": "level2",
        "domain_family": "level2",
        "phase": "aposteriori",
        "start_epoch_ms": start,
        "end_epoch_ms": end,
        "duration_ms": end - start,
        "status": "success",
        "exit_code": 0,
        "first_level2_start_epoch_ms": ts - 7700,
        "latest_level1_end_epoch_ms": ts - 7750
    })

with open(RESULTS / "metrics/runtime_events.jsonl", "w", encoding="utf-8") as f:
    for ev in events:
        f.write(json.dumps(ev) + "\n")
print(f"  [OK] results/metrics/runtime_events.jsonl  ({len(events)} events)")

write(RESULTS / "metrics/run_context.json", {
    "dataset_id": "DS11_single_point_of_failure_basic",
    "mode": "aposteriori",
    "python_executable": "C:/Users/paulc/AppData/Local/Programs/Python/Python313/python.exe",
    "mas_start_epoch_ms": ts - 8200,
    "expected_level1_runs": 31,
    "git_commit": "4738a68"
})

# ── diagnostic_report.txt ────────────────────────────────────────────────────

print("\n=== diagnostic_report.txt ===")

from datetime import datetime
ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

report = f"""
{'='*64}
  Run: {ts_str}  |  Mode: aposteriori  |  Model: llama3.2:3b
  L1 active: 5  |  L2 triggered: 1
{'='*64}
The primary operational issue concerns resource res_firewall_01, which acts as a critical single point of failure in the current infrastructure. Four independent Level-1 detectors converge on this resource: it presents an abnormally low connectivity degree (1 link), carries no visible redundancy, hosts downstream dependencies for at least four services, and sits on a topologically incomplete network link. The Level-2 Single Point of Failure diagnoser assigns it a priority score of 70 (reliability 75, severity 63), indicating a high-confidence, moderately severe finding. The recommended immediate action is to audit res_firewall_01 for missing failover paths, correct the incomplete link declaration in the knowledge graph, and provision a redundant firewall unit or hot-standby before the next maintenance window. No change-induced causation, cascade, or traceability breakdown patterns were detected in this observation window.
"""

report_path = ROOT / "diagnostic_report.txt"
with open(report_path, "a", encoding="utf-8") as f:
    f.write(report)
print(f"  [OK] diagnostic_report.txt")

print(f"\nDone. All mock output files created for DS11 SPOF demo.")
