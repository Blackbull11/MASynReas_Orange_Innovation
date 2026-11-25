/*
 * Criticality vs Structural Weakness Detector - Structural / A Priori
 *
 * This agent detects critical applications whose visible technical support
 * appears too weak with respect to their business importance.
 *
 * Such cases may indicate single points of failure, incomplete infrastructure
 * mapping, weak resilience design, or architectural inconsistencies.
 */

+selected_mode(apriori)
  <- .print("[CriticalityStructuralWeaknessDetector] Starting detection...");
     run_python("src/agt/structural/apriori/criticality_structural_weakness_detector.py");
     .print("[CriticalityStructuralWeaknessDetector] Detection finished.") .

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
