/*
 * Incomplete Network Link Detector - Structural / A Priori
 *
 * This agent detects network links with fewer than two termination resources
 * in the knowledge graph.
 */

+selected_mode(apriori)
  <- .print("[IncompleteNetworkLinkDetector] Starting detection...");
     run_python("src/agt/structural/apriori/incomplete_network_link_detector.py");
     .print("[IncompleteNetworkLinkDetector] Detection finished.") .

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
