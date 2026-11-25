/*
 * Isolated Incident Resource Detector - Structural / A Posteriori
 *
 * This level-1 executor agent detects incident-related resources with little
 * or no network connectivity in the NORIA-O knowledge graph.
 */

+selected_mode(aposteriori)
  <- .print("[IsolatedIncidentResourceDetector] Starting detection...");
     run_python("src/agt/structural/aposteriori/isolated_incident_resource_detector.py");
     .print("[IsolatedIncidentResourceDetector] Detection finished.").

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
