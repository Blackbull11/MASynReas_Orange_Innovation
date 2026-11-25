/*
 * Repeated Similar Event Detector - Dynamic / A Posteriori
 *
 * This level-1 executor agent detects repeated similar events affecting
 * the same related element within a short time window.
 */

+selected_mode(aposteriori)
  <- .print("[RepeatedSimilarEventDetector] Starting detection...");
     run_python("src/agt/dynamic/aposteriori/repeated_similar_event_detector.py");
     .print("[RepeatedSimilarEventDetector] Detection finished.").

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
