/*
 * Flapping State Detector - Dynamic / A Posteriori
 *
 * This level-1 executor agent detects rapid alternation of contradictory
 * state-related events (e.g. UP/DOWN) affecting the same related element.
 */

+selected_mode(aposteriori)
  <- .print("[FlappingStateDetector] Starting detection...");
     run_python("src/agt/dynamic/aposteriori/flapping_state_detector.py");
     .print("[FlappingStateDetector] Detection finished.").

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
