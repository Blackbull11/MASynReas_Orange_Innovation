/*
 * Functional Mapping Gap Diagnoser - Level 2 / A Priori
 */

+!run
  <- .print("[FunctionalMappingGapDiagnoser] Starting diagnosis...");
     run_python("src/agt/level2/apriori/functional_mapping_gap_diagnoser.py");
     .print("[FunctionalMappingGapDiagnoser] Diagnosis finished.");
     .send(level2_controller, tell, l2_agent_done(functional_mapping_gap_diagnoser)).

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
