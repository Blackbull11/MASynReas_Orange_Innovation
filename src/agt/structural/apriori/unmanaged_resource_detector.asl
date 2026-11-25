/*
 * Unmanaged Resource Detector - Structural / A Priori
 *
 * This agent detects resources that are not assigned to any management unit
 * in the NORIA-O knowledge graph.
 *
 * Such resources may indicate missing ownership, incomplete governance
 * modeling, or escalation weaknesses in the ICT infrastructure.
 */

+selected_mode(apriori)
  <- .print("[UnmanagedResourceDetector] Starting detection...");
     run_python("src/agt/structural/apriori/unmanaged_resource_detector.py");
     .print("[UnmanagedResourceDetector] Detection finished.") .

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
