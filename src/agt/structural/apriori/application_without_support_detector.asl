/*
 * Application Without Infrastructure Support Detector - Structural / A Priori
 *
 * This agent detects applications that are not linked to any supporting
 * technical resource in the NORIA-O knowledge graph.
 *
 * Such applications may indicate missing deployment information, incomplete
 * functional-to-technical mapping, or architectural inconsistencies.
 */

+selected_mode(apriori)
  <- .print("[ApplicationWithoutSupportDetector] Starting detection...");
     run_python("src/agt/structural/apriori/application_without_support_detector.py");
     .print("[ApplicationWithoutSupportDetector] Detection finished.") .

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
