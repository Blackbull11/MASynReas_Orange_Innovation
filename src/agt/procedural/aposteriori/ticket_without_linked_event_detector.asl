/*
 * Ticket Without Linked Event Detector - Procedural / A Posteriori
 *
 * This agent detects TroubleTicket instances that are not linked
 * to any EventRecord in the NORIA-O knowledge graph.
 *
 * Such tickets may indicate incidents that were opened manually or
 * incompletely documented, without any observable event trace,
 * reducing the quality of diagnosis and operational traceability.
 */

+selected_mode(aposteriori)
  <- .print("[TicketWithoutLinkedEventDetector] Starting detection...");
     run_python("src/agt/procedural/aposteriori/ticket_without_linked_event_detector.py");
     .print("[TicketWithoutLinkedEventDetector] Detection finished.") .

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
