/*
 * Hidden Service Dependency Detector - Functional / A Posteriori
 *
 * This agent detects situations where a single technical incident may affect
 * multiple services through a shared application support chain, even though
 * no explicit dependency is modeled between these services.
 *
 * In the NORIA-O graph, this is operationalized as:
 * - an event originates from a resource,
 * - that resource supports an application,
 * - one module of that application is attached to two different services,
 * - and no explicit hierarchy/dependency relation is declared between them.
 *
 * Such a pattern may reveal an implicit or hidden dependency between services.
 */

+selected_mode(aposteriori)
  <- .print("[HiddenServiceDependencyDetector] Starting detection...");
     run_python("src/agt/functional/aposteriori/hidden_service_dependency_detector.py");
     .print("[HiddenServiceDependencyDetector] Detection finished.") .

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
