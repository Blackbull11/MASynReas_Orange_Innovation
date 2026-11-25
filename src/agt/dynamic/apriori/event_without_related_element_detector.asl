/*
 * Event Without Related Element Detector - Dynamic / A Priori
 *
 * This level-1 executor agent detects EventRecord instances that are not
 * linked to any related network element, making dynamic diagnosis difficult.
 */

+selected_mode(apriori)
  <- .print("[EventWithoutRelatedElementDetector] Starting detection...");
     run_python("src/agt/dynamic/apriori/event_without_related_element_detector.py");
     .print("[EventWithoutRelatedElementDetector] Detection finished.").

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
