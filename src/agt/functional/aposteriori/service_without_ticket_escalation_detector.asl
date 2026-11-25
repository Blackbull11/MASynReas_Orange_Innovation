/*
 * Service Without Ticket Escalation Detector - Functional / A Posteriori
 *
 * This agent detects services that are impacted by technical events through
 * the functional chain (resource → application → module → service), but for
 * which no related trouble ticket has been opened on the supporting resources.
 *
 * Such patterns may indicate:
 * - missing escalation,
 * - incomplete incident handling,
 * - monitoring without operational follow-up,
 * - or weak coupling between supervision and ticketing.
 */

+selected_mode(aposteriori)
  <- .print("[ServiceWithoutTicketEscalationDetector] Starting detection...");
     run_python("src/agt/functional/aposteriori/service_without_ticket_escalation_detector.py");
     .print("[ServiceWithoutTicketEscalationDetector] Detection finished.") .

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
