/*
 * Missing Parent Resource Detector - Structural / A Priori
 *
 * This agent detects component-like resources that do not have any structural
 * parent in the knowledge graph.
 */

+selected_mode(apriori)
  <- .print("[MissingParentResourceDetector] Starting detection...");
     run_python("src/agt/structural/apriori/missing_parent_resource_detector.py");
     .print("[MissingParentResourceDetector] Detection finished.") .

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
