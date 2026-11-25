/*
 * Event Without Timestamp Detector - Dynamic / A Priori
 *
 * This level-1 executor agent detects EventRecord instances that do not
 * provide any logging timestamp, making temporal reasoning impossible.
 */

+selected_mode(apriori)
  <- .print("[EventWithoutTimestampDetector] Starting detection...");
     run_python("src/agt/dynamic/apriori/event_without_timestamp_detector.py");
     .print("[EventWithoutTimestampDetector] Detection finished.").

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
