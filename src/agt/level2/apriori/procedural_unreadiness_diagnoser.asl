/*
 * Procedural Unreadiness Diagnoser - Level 2 / A Priori
 */

+!run
  <- .print("[ProceduralUnreadinessDiagnoser] Starting diagnosis...");
     run_python("src/agt/level2/apriori/procedural_unreadiness_diagnoser.py");
     .print("[ProceduralUnreadinessDiagnoser] Diagnosis finished.");
     .send(level2_controller, tell, l2_agent_done(procedural_unreadiness_diagnoser)).

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
