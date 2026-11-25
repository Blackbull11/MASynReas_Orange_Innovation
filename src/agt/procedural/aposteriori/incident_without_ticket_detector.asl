/*
 * Incident Without Ticket Detector - Procedural / A Posteriori
 *
 * This agent detects incident-like EventRecord instances that are not linked
 * to any TroubleTicket in the NORIA-O knowledge graph.
 *
 * Such events may indicate operational incidents that were observed by the
 * supervision system but never formalized in the incident management process,
 * leading to a loss of traceability and weaker diagnostic capability.
 */

+selected_mode(aposteriori)
  <- .print("[IncidentWithoutTicketDetector] Starting detection...");
     run_python("src/agt/procedural/aposteriori/incident_without_ticket_detector.py");
     .print("[IncidentWithoutTicketDetector] Detection finished.") .

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
