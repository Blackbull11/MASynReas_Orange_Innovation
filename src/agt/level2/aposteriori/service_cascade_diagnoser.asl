/*
 * Service Cascade Diagnoser - Level 2 / A Posteriori
 */

+!run
  <- .print("[ServiceCascadeDiagnoser] Starting diagnosis...");
     run_python("src/agt/level2/aposteriori/service_cascade_diagnoser.py");
     .print("[ServiceCascadeDiagnoser] Diagnosis finished.");
     .send(level2_controller, tell, l2_agent_done(service_cascade_diagnoser)).

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
