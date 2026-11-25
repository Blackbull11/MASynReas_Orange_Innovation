/*
 * Incident Propagation Detector - Dynamic / A Posteriori
 *
 * This level-1 executor agent detects local incident propagation patterns,
 * where an event affecting one element is shortly followed by an event
 * affecting a structurally adjacent element.
 */

+selected_mode(aposteriori)
  <- .print("[IncidentPropagationDetector] Starting detection...");
     run_python("src/agt/dynamic/aposteriori/incident_propagation_detector.py");
     .print("[IncidentPropagationDetector] Detection finished.").

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
