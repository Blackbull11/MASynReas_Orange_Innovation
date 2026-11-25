/*
 * Cascading Service Failure Detector - Functional / A Posteriori
 *
 * This agent detects situations where an event occurring on a technical
 * resource may propagate to multiple services through a shared application
 * and its modules.
 *
 * In the NORIA-O toy graph, this is operationalized as:
 * - an event is emitted by a resource,
 * - that resource supports an application,
 * - one module of that application is attached to at least two services.
 *
 * Such a pattern suggests that a failure affecting one support chain may
 * propagate functionally to multiple services, which is a useful proxy
 * for cascading service failure in a level-1 deterministic detector.
 */

+selected_mode(aposteriori)
  <- .print("[CascadingServiceFailureDetector] Starting detection...");
     run_python("src/agt/functional/aposteriori/cascading_service_failure_detector.py");
     .print("[CascadingServiceFailureDetector] Detection finished.") .

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
