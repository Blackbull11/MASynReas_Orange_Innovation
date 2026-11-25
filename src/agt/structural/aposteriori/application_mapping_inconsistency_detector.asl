/*
 * Application Mapping Inconsistency Detector - Structural / A Posteriori
 *
 * This level-1 executor agent detects incidents involving applications whose
 * technical support mapping is incomplete or ambiguous in the NORIA-O
 * knowledge graph.
 */

+selected_mode(aposteriori)
  <- .print("[ApplicationMappingInconsistencyDetector] Starting detection...");
     run_python("src/agt/structural/aposteriori/application_mapping_inconsistency_detector.py");
     .print("[ApplicationMappingInconsistencyDetector] Detection finished.").

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
