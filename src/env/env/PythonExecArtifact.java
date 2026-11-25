package env;

import cartago.Artifact;
import cartago.OPERATION;
import cartago.ObsProperty;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Properties;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.Stream;

public class PythonExecArtifact extends Artifact {
    private String pythonExecutable;
    private String selectedMode;
    private String datasetId;
    private long masStartEpochMs;
    private long latestLevel1EndEpochMs = -1L;
    private long firstLevel2StartEpochMs = -1L;
    private Path metricsDirectory;
    private Path runtimeEventsPath;
    private Path runContextPath;

    void init() {
        clearResultsDirectory();
        masStartEpochMs = System.currentTimeMillis();
        defineObsProperty("last_run_status", "idle");

        Properties config = loadConfiguration();
        pythonExecutable = readConfiguredPythonExecutable(config);
        selectedMode = readConfiguredMode(config);
        datasetId = readConfiguredDatasetId(config);

        defineObsProperty("selected_mode", selectedMode);
        defineObsProperty("dataset_id", datasetId);
        defineObsProperty("expected_mode_runs", selectedMode, countPythonDetectors(selectedMode));

        initializeMetricsLogging();
    }

    // ── Single-script operation (legacy, kept for compatibility) ─────────────

    @OPERATION
    public void run_python(String scriptPath) {
        String normalizedPath = normalizeScriptPath(scriptPath);
        long[] res = execProcess(normalizedPath);
        int exitCode = (int) res[0];
        long startMs = res[1], endMs = res[2];
        boolean isLevel2 = normalizedPath.contains("/level2/");

        if (!isLevel2) latestLevel1EndEpochMs = Math.max(latestLevel1EndEpochMs, endMs);

        appendRuntimeEvent(buildScriptEventJson(
                "script_finished", normalizedPath,
                Paths.get(normalizedPath).getFileName().toString(),
                isLevel2 ? "level2" : "level1",
                inferDomainFamily(normalizedPath), inferPhase(normalizedPath),
                startMs, endMs, endMs - startMs, exitCode,
                exitCode == 0 ? "success" : "failure"));

        if (exitCode == 0) {
            getObsProperty("last_run_status").updateValue("success");
            signal("python_finished", scriptPath, exitCode);
        } else {
            getObsProperty("last_run_status").updateValue("failure");
            signal("python_failed", scriptPath, exitCode);
            failed("Python script failed with exit code " + exitCode);
        }
    }

    // ── Parallel pipeline operation ──────────────────────────────────────────

    @OPERATION
    public void run_all_parallel() {
        List<String> l1Scripts = findScripts(selectedMode, false);
        int n = l1Scripts.size();
        log("[PythonExecArtifact] Starting parallel L1: " + n + " scripts, mode=" + selectedMode);

        // Run all L1 scripts in parallel Java threads
        ExecutorService exec = Executors.newFixedThreadPool(Math.min(n, 32));
        Map<String, long[]> results = new ConcurrentHashMap<>();
        CountDownLatch latch = new CountDownLatch(n);

        for (String path : l1Scripts) {
            exec.submit(() -> {
                results.put(path, execProcess(path));
                latch.countDown();
            });
        }

        try { latch.await(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        exec.shutdown();

        // Emit signals and log events from the operation thread (single-threaded, safe)
        for (String path : l1Scripts) {
            long[] res = results.getOrDefault(path, new long[]{-1, masStartEpochMs, System.currentTimeMillis()});
            int code = (int) res[0];
            long startMs = res[1], endMs = res[2];
            latestLevel1EndEpochMs = Math.max(latestLevel1EndEpochMs, endMs);
            appendRuntimeEvent(buildScriptEventJson(
                    "script_finished", path,
                    Paths.get(path).getFileName().toString(), "level1",
                    inferDomainFamily(path), inferPhase(path),
                    startMs, endMs, endMs - startMs, code, code == 0 ? "success" : "failure"));
            if (code == 0) signal("python_finished", path, 0);
            else signal("python_failed", path, code);
        }

        log("[PythonExecArtifact] L1 complete (" + l1Scripts.size()
                + " scripts). Starting L2 for mode=" + selectedMode);

        // L2 scripts run sequentially (they aggregate L1 results)
        List<String> l2Scripts = findScripts(selectedMode, true);
        if (!l2Scripts.isEmpty() && firstLevel2StartEpochMs < 0L) {
            firstLevel2StartEpochMs = System.currentTimeMillis();
        }
        for (String path : l2Scripts) {
            long[] res = execProcess(path);
            int code = (int) res[0];
            long startMs = res[1], endMs = res[2];
            appendRuntimeEvent(buildScriptEventJson(
                    "script_finished", path,
                    Paths.get(path).getFileName().toString(), "level2",
                    "level2", inferPhase(path),
                    startMs, endMs, endMs - startMs, code, code == 0 ? "success" : "failure"));
            if (code == 0) signal("python_finished", path, 0);
            else signal("python_failed", path, code);
        }

        getObsProperty("last_run_status").updateValue("success");
        log("[PythonExecArtifact] Pipeline complete. L1=" + l1Scripts.size()
                + " L2=" + l2Scripts.size() + ". Run: python diagnosis_llm.py");
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    private long[] execProcess(String relativePath) {
        File projectRoot = Paths.get("").toAbsolutePath().toFile();
        File scriptFile = new File(projectRoot, relativePath.replace("/", File.separator));
        long startMs = System.currentTimeMillis();

        if (!scriptFile.exists()) {
            log("[PythonExecArtifact] WARN: script not found: " + scriptFile.getAbsolutePath());
            return new long[]{-1, startMs, System.currentTimeMillis()};
        }

        try {
            ProcessBuilder pb = new ProcessBuilder(pythonExecutable, scriptFile.getAbsolutePath());
            pb.directory(projectRoot);
            pb.redirectErrorStream(true);
            Process proc = pb.start();

            // Drain stdout in a daemon thread to prevent blocking
            Thread drainer = new Thread(() -> {
                try (BufferedReader r = new BufferedReader(
                        new InputStreamReader(proc.getInputStream()))) {
                    String line;
                    while ((line = r.readLine()) != null) {
                        System.out.println("[" + scriptFile.getName() + "] " + line);
                    }
                } catch (IOException ignored) {}
            });
            drainer.setDaemon(true);
            drainer.start();

            int code = proc.waitFor();
            drainer.join(500);
            long endMs = System.currentTimeMillis();
            return new long[]{code, startMs, endMs};
        } catch (Exception e) {
            log("[PythonExecArtifact] Error running " + relativePath + ": " + e.getMessage());
            return new long[]{-1, startMs, System.currentTimeMillis()};
        }
    }

    private List<String> findScripts(String mode, boolean level2) {
        Path agentsRoot = Paths.get("").toAbsolutePath().resolve("src").resolve("agt");
        List<String> scripts = new ArrayList<>();
        if (!Files.exists(agentsRoot)) return scripts;
        Path projectRoot = Paths.get("").toAbsolutePath();
        try (Stream<Path> stream = Files.walk(agentsRoot)) {
            stream.filter(Files::isRegularFile)
                  .filter(p -> p.toString().endsWith(".py"))
                  .filter(p -> p.toString().contains(File.separator + mode + File.separator))
                  .filter(p -> level2
                          ? p.toString().contains(File.separator + "level2" + File.separator)
                          : !p.toString().contains(File.separator + "level2" + File.separator))
                  .sorted()
                  .forEach(p -> scripts.add(
                          projectRoot.relativize(p).toString().replace("\\", "/")));
        } catch (IOException e) {
            log("[PythonExecArtifact] findScripts error: " + e.getMessage());
        }
        return scripts;
    }

    private String normalizeScriptPath(String scriptPath) {
        String p = scriptPath == null ? "" : scriptPath.trim();
        if (p.startsWith("python3 ")) return p.substring(8).trim();
        if (p.startsWith("python "))  return p.substring(7).trim();
        return p;
    }

    private boolean isLevel2Script(String path) {
        return path.replace("\\", "/").contains("/level2/");
    }

    private String inferDomainFamily(String path) {
        String p = path.replace("\\", "/");
        if (p.contains("/structural/")) return "structural";
        if (p.contains("/dynamic/"))    return "dynamic";
        if (p.contains("/functional/")) return "functional";
        if (p.contains("/procedural/")) return "procedural";
        if (p.contains("/level2/"))     return "level2";
        return "unknown";
    }

    private String inferPhase(String path) {
        String p = path.replace("\\", "/");
        if (p.contains("/apriori/"))     return "apriori";
        if (p.contains("/aposteriori/")) return "aposteriori";
        return selectedMode != null ? selectedMode : "unknown";
    }

    private void clearResultsDirectory() {
        try {
            Path resultsDir = Paths.get("").toAbsolutePath().resolve("results").normalize();
            if (!Files.exists(resultsDir)) {
                Files.createDirectories(resultsDir);
                return;
            }
            Files.walk(resultsDir)
                    .sorted(Comparator.reverseOrder())
                    .filter(path -> !path.equals(resultsDir))
                    .forEach(this::deletePath);
            Files.createDirectories(resultsDir);
            log("[PythonExecArtifact] Cleared results directory: " + resultsDir);
        } catch (Exception e) {
            failed("Could not clear results directory: " + e.getMessage());
        }
    }

    private Properties loadConfiguration() {
        Path configPath = Paths.get("").toAbsolutePath().resolve("mas.properties");
        Properties properties = new Properties();
        if (!Files.exists(configPath)) {
            failed("MAS configuration file not found: " + configPath);
            return properties;
        }
        try (InputStream is = Files.newInputStream(configPath)) {
            properties.load(is);
        } catch (IOException e) {
            failed("Could not read MAS configuration file: " + e.getMessage());
        }
        return properties;
    }

    private String readConfiguredMode(Properties p) {
        String mode = p.getProperty("mode", "").trim().toLowerCase(Locale.ROOT);
        if (!"apriori".equals(mode) && !"aposteriori".equals(mode)) {
            failed("Invalid mode in mas.properties: " + mode);
            return "apriori";
        }
        log("[PythonExecArtifact] mode=" + mode);
        return mode;
    }

    private String readConfiguredDatasetId(Properties p) {
        String id = p.getProperty("dataset.id", "").trim();
        if (id.isEmpty()) return "unspecified";
        log("[PythonExecArtifact] dataset.id=" + id);
        return id;
    }

    private String readConfiguredPythonExecutable(Properties p) {
        String configured = p.getProperty("python.path", "").trim();
        if (!configured.isEmpty() && Files.exists(Paths.get(configured))) {
            log("[PythonExecArtifact] python=" + configured);
            return configured;
        }
        String fallback = findAvailablePythonExecutable();
        if (fallback != null) {
            log("[PythonExecArtifact] python fallback=" + fallback);
            return fallback;
        }
        failed("No Python interpreter found. Set python.path in mas.properties.");
        return "python";
    }

    private String findAvailablePythonExecutable() {
        for (String c : new String[]{"python", "python3"}) {
            if (isRunnablePython(c)) return c;
        }
        return null;
    }

    private boolean isRunnablePython(String candidate) {
        try {
            return new ProcessBuilder(candidate, "--version")
                    .redirectErrorStream(true).start().waitFor() == 0;
        } catch (Exception e) { return false; }
    }

    private void initializeMetricsLogging() {
        try {
            metricsDirectory = Paths.get("").toAbsolutePath().resolve("results").resolve("metrics");
            Files.createDirectories(metricsDirectory);
            runtimeEventsPath = metricsDirectory.resolve("runtime_events.jsonl");
            runContextPath    = metricsDirectory.resolve("run_context.json");
            Files.deleteIfExists(runtimeEventsPath);
            Files.writeString(runContextPath, buildRunContextJson(),
                    StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
            appendRuntimeEvent(buildMasStartEventJson());
        } catch (Exception e) {
            log("[PythonExecArtifact] Metrics init failed: " + e.getMessage());
        }
    }

    private void appendRuntimeEvent(String jsonLine) {
        if (runtimeEventsPath == null) return;
        try {
            Files.writeString(runtimeEventsPath, jsonLine + System.lineSeparator(),
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (IOException e) {
            log("[PythonExecArtifact] Could not append runtime event: " + e.getMessage());
        }
    }

    private String buildRunContextJson() {
        return "{\n"
                + "  \"dataset_id\": \"" + escapeJson(datasetId) + "\",\n"
                + "  \"mode\": \"" + escapeJson(selectedMode) + "\",\n"
                + "  \"python_executable\": \"" + escapeJson(pythonExecutable) + "\",\n"
                + "  \"mas_start_epoch_ms\": " + masStartEpochMs + ",\n"
                + "  \"expected_level1_runs\": " + countPythonDetectors(selectedMode) + ",\n"
                + "  \"git_commit\": \"" + escapeJson(readGitCommit()) + "\"\n"
                + "}\n";
    }

    private String buildMasStartEventJson() {
        return "{\"event\":\"mas_started\","
                + "\"dataset_id\":\"" + escapeJson(datasetId) + "\","
                + "\"mode\":\"" + escapeJson(selectedMode) + "\","
                + "\"epoch_ms\":" + masStartEpochMs + "}";
    }

    private String buildScriptEventJson(
            String event, String scriptPath, String scriptName,
            String catalogueLevel, String domainFamily, String phase,
            long startMs, long endMs, long durationMs, int exitCode, String status) {
        StringBuilder sb = new StringBuilder("{");
        sb.append("\"event\":\"").append(escapeJson(event)).append("\",");
        sb.append("\"dataset_id\":\"").append(escapeJson(datasetId)).append("\",");
        sb.append("\"mode\":\"").append(escapeJson(selectedMode)).append("\",");
        sb.append("\"script_path\":\"").append(escapeJson(scriptPath)).append("\",");
        sb.append("\"script_name\":\"").append(escapeJson(scriptName)).append("\",");
        sb.append("\"catalogue_level\":\"").append(escapeJson(catalogueLevel)).append("\",");
        sb.append("\"domain_family\":\"").append(escapeJson(domainFamily)).append("\",");
        sb.append("\"phase\":\"").append(escapeJson(phase)).append("\",");
        sb.append("\"start_epoch_ms\":").append(startMs).append(",");
        sb.append("\"end_epoch_ms\":").append(endMs).append(",");
        sb.append("\"duration_ms\":").append(durationMs).append(",");
        sb.append("\"status\":\"").append(escapeJson(status)).append("\"");
        if (exitCode != Integer.MIN_VALUE) sb.append(",\"exit_code\":").append(exitCode);
        if (firstLevel2StartEpochMs >= 0L)
            sb.append(",\"first_level2_start_epoch_ms\":").append(firstLevel2StartEpochMs);
        if (latestLevel1EndEpochMs >= 0L)
            sb.append(",\"latest_level1_end_epoch_ms\":").append(latestLevel1EndEpochMs);
        sb.append("}");
        return sb.toString();
    }

    private String readGitCommit() {
        try {
            Process p = new ProcessBuilder("git", "rev-parse", "HEAD")
                    .directory(Paths.get("").toAbsolutePath().toFile())
                    .redirectErrorStream(true).start();
            try (BufferedReader r = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
                String line = r.readLine();
                if (p.waitFor() == 0 && line != null) return line.trim();
            }
        } catch (Exception ignored) {}
        return "";
    }

    private String escapeJson(String v) {
        if (v == null) return "";
        return v.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\r", "\\r").replace("\n", "\\n");
    }

    private int countPythonDetectors(String mode) {
        Path agentsRoot = Paths.get("").toAbsolutePath().resolve("src").resolve("agt");
        if (!Files.exists(agentsRoot)) return 0;
        try (Stream<Path> s = Files.walk(agentsRoot)) {
            return (int) s.filter(Files::isRegularFile)
                    .filter(p -> p.toString().endsWith(".py"))
                    .filter(p -> p.toString().contains(File.separator + mode + File.separator))
                    .filter(p -> !p.toString().contains(File.separator + "level2" + File.separator))
                    .count();
        } catch (IOException e) {
            return 0;
        }
    }

    private void deletePath(Path path) {
        try { Files.deleteIfExists(path); }
        catch (IOException e) { throw new RuntimeException("Could not delete " + path, e); }
    }
}
