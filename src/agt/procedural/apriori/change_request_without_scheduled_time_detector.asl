/*
 * Change Request Without Scheduled Time Detector - Procedural / A Priori
 *
 * This agent detects ChangeRequest instances that do not have any
 * scheduled execution time in the NORIA-O knowledge graph.
 *
 * Such changes may indicate poor planning and can introduce risks
 * when executed without a defined time window.
 */

+selected_mode(apriori)
  <- .print("[ChangeRequestWithoutScheduledTimeDetector] Starting detection...");
     run_python("src/agt/procedural/apriori/change_request_without_scheduled_time_detector.py");
     .print("[ChangeRequestWithoutScheduledTimeDetector] Detection finished.") .

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
