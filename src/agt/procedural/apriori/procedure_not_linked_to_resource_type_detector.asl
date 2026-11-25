/*
 * Procedure Not Linked To Resource Type Detector - Procedural / A Priori
 *
 * This agent detects procedures that are not linked to any resource type
 * in the NORIA-O knowledge graph.
 *
 * In practice, this detector operationalizes the notion of "linked to a
 * resource type" through the absence of any event recommending the procedure
 * on a resource carrying a noria:resourceType.
 */

+selected_mode(apriori)
  <- .print("[ProcedureNotLinkedToResourceTypeDetector] Starting detection...");
     run_python("src/agt/procedural/apriori/procedure_not_linked_to_resource_type_detector.py");
     .print("[ProcedureNotLinkedToResourceTypeDetector] Detection finished.") .

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
