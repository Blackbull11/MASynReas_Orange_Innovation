/*
 * Critical Event Ticket Escalation Detector - Dynamic / A Posteriori
 *
 * This level-1 executor agent detects patterns where a critical-like event
 * is followed by the opening of a high-severity / high-priority / high-urgency
 * trouble ticket triggered by that event.
 */

+selected_mode(aposteriori)
  <- .print("[CriticalEventTicketEscalationDetector] Starting detection...");
     run_python("src/agt/dynamic/aposteriori/critical_event_ticket_escalation_detector.py");
     .print("[CriticalEventTicketEscalationDetector] Detection finished.").

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
