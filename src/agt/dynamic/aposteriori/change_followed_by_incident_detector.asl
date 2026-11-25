/*
 * Change Followed By Incident Detector - Dynamic / A Posteriori
 *
 * This level-1 executor agent detects patterns where a ChangeRequest
 * is followed shortly afterwards by an EventRecord on the same related element.
 */

+selected_mode(aposteriori)
  <- .print("[ChangeFollowedByIncidentDetector] Starting detection...");
     run_python("src/agt/dynamic/aposteriori/change_followed_by_incident_detector.py");
     .print("[ChangeFollowedByIncidentDetector] Detection finished.").

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
