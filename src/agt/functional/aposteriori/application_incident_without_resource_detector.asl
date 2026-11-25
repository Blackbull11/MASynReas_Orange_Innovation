/*
 * Application Incident Without Resource Detector - Functional / A Posteriori
 *
 * This agent detects application-level incidents or event records whose
 * originating management system is an application that is not linked to any
 * supporting resource in the NORIA-O knowledge graph.
 *
 * Such a pattern may indicate a functional incident occurring on an application
 * that is not grounded in the technical layer, which can reveal missing
 * deployment information, incomplete ingestion of dependencies, or an
 * inconsistency between functional supervision and infrastructure mapping.
 */

+selected_mode(aposteriori)
  <- .print("[ApplicationIncidentWithoutResourceDetector] Starting detection...");
     run_python("src/agt/functional/aposteriori/application_incident_without_resource_detector.py");
     .print("[ApplicationIncidentWithoutResourceDetector] Detection finished.") .

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
