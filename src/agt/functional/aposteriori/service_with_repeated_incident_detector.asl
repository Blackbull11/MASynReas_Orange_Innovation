/*
 * Service With Repeated Incident Detector - Functional / A Posteriori
 *
 * This agent detects services that are impacted repeatedly by technical events
 * through the functional chain (resource → application → module → service).
 *
 * Such patterns may indicate:
 * - chronic service fragility,
 * - recurring degradation,
 * - repeated infrastructure stress,
 * - or unresolved root causes.
 */

+selected_mode(aposteriori)
  <- .print("[ServiceWithRepeatedIncidentDetector] Starting detection...");
     run_python("src/agt/functional/aposteriori/service_with_repeated_incident_detector.py");
     .print("[ServiceWithRepeatedIncidentDetector] Detection finished.") .

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
