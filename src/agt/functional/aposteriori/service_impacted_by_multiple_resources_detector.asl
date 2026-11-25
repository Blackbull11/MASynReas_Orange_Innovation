/*
 * Service Impacted By Multiple Resources Detector - Functional / A Posteriori
 *
 * This agent detects services that are impacted by multiple distinct resources
 * through the functional chain (resource → application → module → service).
 *
 * Such patterns typically indicate:
 * - major incidents,
 * - distributed failures,
 * - or systemic degradation affecting a service.
 */

+selected_mode(aposteriori)
  <- .print("[ServiceImpactedByMultipleResourcesDetector] Starting detection...");
     run_python("src/agt/functional/aposteriori/service_impacted_by_multiple_resources_detector.py");
     .print("[ServiceImpactedByMultipleResourcesDetector] Detection finished.") .

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
