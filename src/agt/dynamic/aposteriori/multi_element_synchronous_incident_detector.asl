/*
 * Multi Element Synchronous Incident Detector - Dynamic / A Posteriori
 *
 * This level-1 executor agent detects patterns where several distinct
 * related elements are affected by EventRecord instances within a short
 * common time window.
 */

+selected_mode(aposteriori)
  <- .print("[MultiElementSynchronousIncidentDetector] Starting detection...");
     run_python("src/agt/dynamic/aposteriori/multi_element_synchronous_incident_detector.py");
     .print("[MultiElementSynchronousIncidentDetector] Detection finished.").

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
