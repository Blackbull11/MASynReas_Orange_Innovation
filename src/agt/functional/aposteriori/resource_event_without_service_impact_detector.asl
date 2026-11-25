/*
 * Resource Event Without Service Impact Detector - Functional / A Posteriori
 *
 * This agent detects events occurring on resources that cannot be propagated
 * to any service through the functional chain (resource → application → module → service).
 *
 * Such patterns may indicate:
 * - isolated technical incidents,
 * - missing functional mapping,
 * - incomplete knowledge graph,
 * - or non-critical infrastructure alerts.
 */

+selected_mode(aposteriori)
  <- .print("[ResourceEventWithoutServiceImpactDetector] Starting detection...");
     run_python("src/agt/functional/aposteriori/resource_event_without_service_impact_detector.py");
     .print("[ResourceEventWithoutServiceImpactDetector] Detection finished.") .

// Suppress Jason NPE on unhandled observable-property / signal events
+selected_mode(_) <- true.
+last_run_status(_) <- true.
+dataset_id(_) <- true.
+expected_mode_runs(_, _) <- true.
+python_finished(_, _)[artifact_id(_)] <- true.
+python_failed(_, _)[artifact_id(_)] <- true.

// Universal catch-all: prevent Jason NPE on any unhandled belief event
+E <- true.
-E <- true.
