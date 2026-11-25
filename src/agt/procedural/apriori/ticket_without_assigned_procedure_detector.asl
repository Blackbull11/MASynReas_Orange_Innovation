/*
 * Ticket Without Assigned Procedure Detector - Procedural / A Priori
 *
 * This agent detects TroubleTicket instances that are not associated
 * with any suggested or assigned operational procedure in the NORIA-O
 * knowledge graph.
 *
 * In practice, this detector operationalizes the notion of "assigned
 * procedure" through the absence of any procedure proposed from the
 * event(s) linked to the ticket.
 */

+selected_mode(apriori)
  <- .print("[TicketWithoutAssignedProcedureDetector] Starting detection...");
     run_python("src/agt/procedural/apriori/ticket_without_assigned_procedure_detector.py");
     .print("[TicketWithoutAssignedProcedureDetector] Detection finished.") .

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
