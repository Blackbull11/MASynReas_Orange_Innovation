/*
 * Traceability Breakdown Diagnoser - Level 2 / A Posteriori
 */

+!run
  <- .print("[TraceabilityBreakdownDiagnoser] Starting diagnosis...");
     run_python("src/agt/level2/aposteriori/traceability_breakdown_diagnoser.py");
     .print("[TraceabilityBreakdownDiagnoser] Diagnosis finished.");
     .send(level2_controller, tell, l2_agent_done(traceability_breakdown_diagnoser)).

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
