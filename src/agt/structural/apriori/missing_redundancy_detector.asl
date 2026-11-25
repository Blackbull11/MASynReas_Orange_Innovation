/*
 * Missing or Incomplete Redundancy Detector - Structural / A Priori
 *
 * This agent detects critical applications that appear to rely on too few
 * supporting resources in the NORIA-O knowledge graph.
 *
 * Such cases may indicate single points of failure, incomplete redundancy
 * modeling, or resilience weaknesses in the ICT architecture.
 */

+selected_mode(apriori)
  <- .print("[MissingRedundancyDetector] Starting detection...");
     run_python("src/agt/structural/apriori/missing_redundancy_detector.py");
     .print("[MissingRedundancyDetector] Detection finished.") .

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
