/*
 * Service Without Application Detector - Functional / A Priori
 *
 * This level-1 executor agent detects services that are not linked to any
 * application module.
 */

+selected_mode(apriori)
  <- .print("[ServiceWithoutApplicationDetector] Starting detection...");
     run_python("src/agt/functional/apriori/service_without_application_detector.py");
     .print("[ServiceWithoutApplicationDetector] Detection finished.").

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
