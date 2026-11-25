/*
 * Change Without Effective Time Detector - Dynamic / A Priori
 *
 * This level-1 executor agent detects ChangeRequest instances that do not
 * provide complete effective execution times, making post-change temporal
 * diagnosis unreliable.
 */

+selected_mode(apriori)
  <- .print("[ChangeWithoutEffectiveTimeDetector] Starting detection...");
     run_python("src/agt/dynamic/apriori/change_without_effective_time_detector.py");
     .print("[ChangeWithoutEffectiveTimeDetector] Detection finished.").

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
