/*
 * Application Without Resource Detector - Functional / A Priori
 *
 * This level-1 executor agent detects applications that are not linked to
 * any supporting technical resource.
 */

+selected_mode(apriori)
  <- .print("[ApplicationWithoutResourceDetector] Starting detection...");
     run_python("src/agt/functional/apriori/application_without_resource_detector.py");
     .print("[ApplicationWithoutResourceDetector] Detection finished.").

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
