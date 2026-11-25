/*
 * Critical Service Exposure Diagnoser - Level 2 / A Priori
 */

+!run
  <- .print("[CriticalServiceExposureDiagnoser] Starting diagnosis...");
     run_python("src/agt/level2/apriori/critical_service_exposure_diagnoser.py");
     .print("[CriticalServiceExposureDiagnoser] Diagnosis finished.");
     .send(level2_controller, tell, l2_agent_done(critical_service_exposure_diagnoser)).

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
