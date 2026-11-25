/*
 * High Impact Resource Detector - Structural / A Posteriori
 *
 * This level-1 executor agent detects incident-affected resources that occupy
 * a structurally central position in the NORIA-O knowledge graph.
 */

+selected_mode(aposteriori)
  <- .print("[HighImpactResourceDetector] Starting detection...");
     run_python("src/agt/structural/aposteriori/high_impact_resource_detector.py");
     .print("[HighImpactResourceDetector] Detection finished.").

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
