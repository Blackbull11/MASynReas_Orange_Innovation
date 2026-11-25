/*
 * Conflicting Application State Detector - Functional / A Posteriori
 *
 * This agent detects applications that appear in conflicting operational
 * states at the same time, based on event types.
 *
 * A conflict is identified when multiple events with different types are
 * associated to the same application at the same timestamp.
 */

+selected_mode(aposteriori)
  <- .print("[ConflictingApplicationStateDetector] Starting detection...");
     run_python("src/agt/functional/aposteriori/conflicting_application_state_detector.py");
     .print("[ConflictingApplicationStateDetector] Detection finished.") .

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
