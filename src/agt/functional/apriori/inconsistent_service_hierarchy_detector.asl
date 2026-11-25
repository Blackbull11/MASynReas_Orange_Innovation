/*
 * Inconsistent Service Hierarchy Detector - Functional / A Priori
 *
 * This level-1 executor agent detects modules linked to several parent
 * services, which may indicate an inconsistent service hierarchy.
 */

+selected_mode(apriori)
  <- .print("[InconsistentServiceHierarchyDetector] Starting detection...");
     run_python("src/agt/functional/apriori/inconsistent_service_hierarchy_detector.py");
     .print("[InconsistentServiceHierarchyDetector] Detection finished.").

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
