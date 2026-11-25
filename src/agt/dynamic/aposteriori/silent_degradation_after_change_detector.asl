/*
 * Silent Degradation After Change Detector - Dynamic / A Posteriori
 *
 * This level-1 executor agent detects patterns where a completed change is
 * followed by a progressive accumulation of weak or non-critical events on
 * the same related element.
 */

+selected_mode(aposteriori)
  <- .print("[SilentDegradationAfterChangeDetector] Starting detection...");
     run_python("src/agt/dynamic/aposteriori/silent_degradation_after_change_detector.py");
     .print("[SilentDegradationAfterChangeDetector] Detection finished.").

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
