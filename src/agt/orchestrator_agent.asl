/*
 * orchestrator_agent.asl  —  MASynReas pipeline orchestrator
 *
 * Joins workspace w, looks up the pyexec artifact, and calls
 * run_all_parallel() which runs all L1 detectors in parallel Java threads
 * then all L2 diagnosers sequentially.  No 'focus:' in the .jcm so the
 * Jason 3.3.0 VirtualThread NPE (missing jcm::focus_env_art plans) is avoided.
 */

!start.

+!start <-
    .print("[Orchestrator] MASynReas starting...");
    joinWorkspace("/main/w", WId);
    lookupArtifact("pyexec", ArtId)[wid(WId)];
    .print("[Orchestrator] Artifact found. Running L1+L2 detection pipeline...");
    run_all_parallel[artifact_id(ArtId)];
    .print("[Orchestrator] Pipeline complete. Results in results/");
    .print("[Orchestrator] Run:  python diagnosis_llm.py  for the L3 narrative.");
    .stopMAS.

/* Failure handler — prints the error and exits cleanly */
-!start[error(E), error_msg(M)] <-
    .print("[Orchestrator] ERROR in start: ", E, " -- ", M);
    .stopMAS.
