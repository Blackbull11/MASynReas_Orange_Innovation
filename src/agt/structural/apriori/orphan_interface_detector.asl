/*
 * Orphan Interface Detector - Structural / A Priori
 *
 * This agent detects network interfaces that are not attached to any resource.
 *
 * Such interfaces are structurally invalid and typically indicate
 * inconsistencies in the knowledge graph.
 */

+selected_mode(apriori)
  <- .print("[OrphanInterfaceDetector] Starting detection...");
     run_python("src/agt/structural/apriori/orphan_interface_detector.py");
     .print("[OrphanInterfaceDetector] Detection finished.") .

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
