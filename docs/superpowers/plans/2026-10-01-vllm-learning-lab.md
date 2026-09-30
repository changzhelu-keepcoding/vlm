# vLLM Learning Lab Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current vLLM learning prototype into a reproducible CLI learning lab with JSON experiment records, optional WSL2/Docker guidance, versioned upstream source access, and a first-stage learning report.

**Architecture:** Keep the existing boundaries: `client.py` speaks the OpenAI-compatible protocol, `benchmark.py` runs concurrent requests and calculates metrics, `recording.py` persists a complete run snapshot, and `cli.py` composes these pieces. Documentation and PowerShell helpers remain optional edges around the Python core; no web UI or service lifecycle manager is added.

**Tech Stack:** Python 3.10+, standard library only at runtime, `unittest`, `argparse`, `pathlib`, JSON, PowerShell, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-01-vllm-learning-lab-design.md`

## Global Constraints

- The client project supports Windows; WSL2 is the primary vLLM deployment path and Docker is supplementary.
- The first-stage CLI contains only `smoke`, `benchmark`, and experiment recording.
- Runtime code has no third-party Python dependencies.
- A benchmark continues after an individual request fails and records the failure.
- API keys are used only for request headers and are never persisted.
- The baseline is an approximately 1.5B instruct model; every real run records the model and vLLM server version.
- The first benchmark matrix fixes model and prompt and compares concurrency `1/2/4/8`.
- First-stage metrics are success count, failure count, average latency, request throughput, and total tokens.
- p95, TTFT, generated tokens/s, GPU monitoring, and advanced features are follow-up work.
- Upstream source is fetched by version into an external source directory; vLLM source is not copied into the learning package.
- Offline unit tests and simulated experiments must run without a GPU or a live vLLM service.

## Review Focus

- **Secret leakage:** an API key passed to the client must not appear in a JSON run record or Markdown report; test this in the recording task.
- **Partial failure:** one failed request must not cancel the rest of a benchmark; test this in the benchmark/recording tasks.
- **Empty and all-failed runs:** zero prompts and a run where every request fails must produce valid zero-valued metrics rather than divide-by-zero errors; test this in the benchmark task.
- **Protocol irregularity:** a response without `choices` must be reported as a clear protocol error, while missing optional `usage` fields remain valid; test this in the client task and keep the behavior documented.
- **Version and path safety:** source fetching must refuse a dirty existing checkout and must not write outside the requested destination; test the PowerShell helper with syntax and safety checks.

---

### Task 1: Add versioned JSON run records

**Files:**
- Create: `src/vllm_learning_lab/recording.py`
- Create: `tests/test_recording.py`
- Modify: `src/vllm_learning_lab/__init__.py` to export the record types and writer

**Interfaces:**
- Consumes: `BenchmarkSummary` from `src/vllm_learning_lab/benchmark.py`.
- Produces:
  - `RunRecord(run_id: str, created_at: str, client_version: str, server_base_url: str, server_version: str, model: str, prompt: str, total_requests: int, concurrency: int, summary: BenchmarkSummary)`.
  - `RunRecord.to_dict() -> dict[str, object]`.
  - `write_run_record(record: RunRecord, output_dir: pathlib.Path) -> pathlib.Path`.

- [ ] **Step 1: Write the failing tests**

  Add tests named:

  - `test_run_record_serializes_configuration_and_summary`: build a record with a one-failure `BenchmarkSummary`; assert the dictionary contains run id, timestamps, model, server version, concurrency, success/failure counts, latency, throughput, token total, and error text.
  - `test_write_run_record_creates_utf8_json_without_api_key`: write into `TemporaryDirectory`; assert the returned path is `<output_dir>/<run_id>.json`, the JSON is valid UTF-8, and the serialized text does not contain a sample API key because the record interface has no API-key field.
  - `test_write_run_record_creates_missing_directory`: pass a nested non-existing directory and assert the JSON file is created there.

- [ ] **Step 2: Run the recording tests and verify RED**

  Run from the project root:

  ```powershell
  $env:PYTHONPATH = "src"
  python -m unittest tests.test_recording -v
  ```

  Expected: FAIL because `vllm_learning_lab.recording` and its public interfaces do not yet exist.

- [ ] **Step 3: Implement `RunRecord` and `write_run_record`**

  In `recording.py`, use frozen dataclasses and `pathlib.Path`. `to_dict()` must flatten the summary into JSON-native values and include the error list; `write_run_record()` must create parent directories, write `ensure_ascii=False` JSON with stable indentation, and use `record.run_id` as the filename. Do not accept or store an API key.

- [ ] **Step 4: Run the recording tests and verify GREEN**

  ```powershell
  $env:PYTHONPATH = "src"
  python -m unittest tests.test_recording -v
  ```

  Expected: all recording tests PASS.

- [ ] **Step 5: Run the existing full suite**

  ```powershell
  $env:PYTHONPATH = "src"
  python -m unittest discover -s tests -v
  ```

  Expected: the original six tests plus the recording tests PASS.

### Task 2: Persist benchmark runs through the CLI

**Files:**
- Modify: `src/vllm_learning_lab/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_benchmark.py` only if an empty-prompt regression test needs to live beside existing benchmark behavior

**Interfaces:**
- Consumes: `VLLMClient`, `run_benchmark`, `BenchmarkSummary`, `RunRecord`, and `write_run_record`.
- Produces:
  - Benchmark options `--output-dir` (default `runs`) and `--server-version` (default `unknown`, with the live-run documentation requiring the real version).
  - `save_benchmark_run(args: argparse.Namespace, client: VLLMClient, *, run_id: str, created_at: str) -> tuple[BenchmarkSummary, pathlib.Path]`.
  - CLI output containing `saved_run=<path>` after a benchmark.

- [ ] **Step 1: Write the failing tests**

  Add tests named:

  - `test_parser_accepts_recording_options`: parse `benchmark --model demo --output-dir records --server-version vX`; assert both values are preserved.
  - `test_save_benchmark_run_writes_configuration_and_summary`: use a fake client and `TemporaryDirectory`; call `save_benchmark_run`; assert the returned summary is correct, the file exists, and its JSON contains the requested model, prompt, output-independent server metadata, request count, and concurrency.
  - `test_save_benchmark_run_continues_after_failed_request`: use the existing fake client with one failing prompt; assert the JSON contains both successes and the recorded error.

- [ ] **Step 2: Run the CLI tests and verify RED**

  ```powershell
  $env:PYTHONPATH = "src"
  python -m unittest tests.test_cli -v
  ```

  Expected: FAIL because the new parser options and `save_benchmark_run` do not yet exist.

- [ ] **Step 3: Implement the CLI recording seam**

  Add the two benchmark options, keep `smoke` unchanged, and move benchmark orchestration into `save_benchmark_run`. The function should build repeated prompts from `args.requests`, call `run_benchmark`, create a UTC ISO-8601 timestamp and run record supplied by its caller, write the JSON, and return both summary and path. `main()` should generate a UUID run id, print the existing summary followed by `saved_run=...`, and return exit code `1` when failures are present. Never pass `args.api_key` into `RunRecord`.

- [ ] **Step 4: Add edge-case tests for empty and all-failed runs**

  Add tests named `test_empty_prompt_sequence_has_zero_metrics` and `test_all_failed_requests_have_zero_throughput_and_record_errors` in `tests/test_benchmark.py`. Assert no exception, `total_requests` matches input, average latency is `0.0` for an empty run, and all-failed throughput is `0.0` with every error preserved.

- [ ] **Step 5: Implement only the minimal benchmark edge handling**

  In `run_benchmark`, preserve the existing continue-on-error behavior, avoid division by zero for an empty prompt sequence, and calculate throughput from successful requests. Do not add retries or new advanced metrics.

- [ ] **Step 6: Run the focused and full suites**

  ```powershell
  $env:PYTHONPATH = "src"
  python -m unittest tests.test_cli tests.test_benchmark -v
  python -m unittest discover -s tests -v
  ```

  Expected: all tests PASS and the full suite has no warnings or errors.

### Task 3: Add safe upstream source and deployment helpers

**Files:**
- Create: `scripts/fetch_upstream.ps1`
- Create: `source/README.md`
- Create: `deploy/wsl2/README.md`
- Create: `deploy/docker/README.md`
- Create: `deploy/README.md`

**Interfaces:**
- Consumes: a user-provided Git ref and destination path.
- Produces: a versioned vLLM checkout outside the Python package and documented commands for WSL2-first, Docker-second service startup.

- [ ] **Step 1: Write the helper contract checks**

  Add a lightweight `tests/test_project_layout.py` that asserts the three deployment documents and `source/README.md` exist, and that the PowerShell script contains the required `-Ref` parameter, a dirty-check guard, and no API key literal. This test checks the safety contract without cloning a remote repository.

- [ ] **Step 2: Run the layout checks and verify RED**

  ```powershell
  $env:PYTHONPATH = "src"
  python -m unittest tests.test_project_layout -v
  ```

  Expected: FAIL because the helper and deployment documentation do not yet exist.

- [ ] **Step 3: Implement the PowerShell helper**

  `scripts/fetch_upstream.ps1` must accept mandatory `-Ref` and optional `-Destination` (default `source/vllm`). For a new destination, clone the vLLM repository at the requested ref; for an existing checkout, fetch tags and refuse to continue when the worktree is dirty before checking out the requested ref. Write the selected ref to `source/VLLM_VERSION.txt`. Do not delete, reset, or overwrite user changes.

- [ ] **Step 4: Write deployment guidance**

  Document the WSL2 primary path and Docker supplementary path with placeholders the user must fill (`<model-name>`, actual server version, and API key). Explain that the learning client can run on Windows while the HTTP service runs in the Linux GPU environment. State that the first live experiment must record the actual vLLM version.

- [ ] **Step 5: Run helper syntax and layout verification**

  ```powershell
  $script = Get-Content -Raw scripts/fetch_upstream.ps1
  [scriptblock]::Create($script) | Out-Null
  $env:PYTHONPATH = "src"
  python -m unittest tests.test_project_layout -v
  ```

  Expected: PowerShell parses successfully and all layout checks PASS.

### Task 4: Finish the learning report and experiment workflow

**Files:**
- Create: `LEARNING_REPORT.md`
- Create: `experiments/runs/.gitkeep`
- Modify: `README.md`
- Modify: `STUDY_LOG.md`
- Modify: `VLLM_LEARNING_PLAN.md`
- Modify: `notes/01-api-path.md`
- Modify: `notes/02-performance-vocabulary.md`

**Interfaces:**
- Consumes: the `vllm-lab smoke` and `vllm-lab benchmark` commands plus JSON files produced by Task 2.
- Produces: a human-readable report template and a documented first experiment workflow.

- [ ] **Step 1: Create the report and run-directory placeholders**

  Add a Markdown report with sections for environment/version, the four concurrency runs, observations, prefill/decode explanation, KV cache explanation, continuous batching explanation, one source call chain, unresolved questions, and next experiment. Add `experiments/runs/.gitkeep` so the intended record directory is visible before the first live run.

- [ ] **Step 2: Update the user workflow documentation**

  Update README and study log examples to include `--output-dir` and `--server-version`, show the four commands for concurrency `1/2/4/8`, explain where JSON is saved, and explicitly state that API keys are not persisted. Update the two notes so their definitions match the accepted glossary in `CONTEXT.md`.

- [ ] **Step 3: Verify documentation references**

  Run:

  ```powershell
  $required = @('LEARNING_REPORT.md','experiments/runs/.gitkeep','README.md','STUDY_LOG.md','VLLM_LEARNING_PLAN.md')
  foreach ($path in $required) { if (-not (Test-Path $path)) { throw "Missing $path" } }
  rg -n -- "--output-dir|--server-version|concurrency 1|concurrency 2|concurrency 4|concurrency 8|API key" README.md STUDY_LOG.md VLLM_LEARNING_PLAN.md LEARNING_REPORT.md
  ```

  Expected: all required files exist and the new workflow terms are present.

### Task 5: Full verification and first-stage handoff

**Files:**
- Modify: `README.md` only if final command output or test instructions need correction.

**Interfaces:**
- Consumes: all components and documentation from Tasks 1–4.
- Produces: a verified learning lab ready for the first real WSL2 experiment.

- [ ] **Step 1: Run the complete offline verification**

  ```powershell
  $env:PYTHONPATH = "src"
  python -m unittest discover -s tests -v
  python -m compileall -q src tests
  python -m vllm_learning_lab --help
  ```

  Expected: all tests PASS, compilation exits `0`, and help lists `smoke` and `benchmark`.

- [ ] **Step 2: Verify the benchmark record path with a simulated client**

  Run the recording and CLI tests again with a temporary output directory; inspect the generated JSON and confirm it contains no API key, includes the chosen model/concurrency/server version, and preserves any failure text.

- [ ] **Step 3: Perform the live smoke check when a service is available**

  Start the documented WSL2 service, run `vllm-lab smoke`, and capture the actual model and vLLM server version in `STUDY_LOG.md`. If no service is available, report this as an unperformed live check rather than treating offline tests as equivalent.

- [ ] **Step 4: Run and record the first experiment matrix**

  Run the same prompt and model at concurrency `1`, `2`, `4`, and `8`; keep each JSON file, then fill the corresponding table and interpretation sections in `LEARNING_REPORT.md`.

- [ ] **Step 5: Complete the first source call-chain note**

  Choose one observed behavior, record the pinned vLLM version, file path, function/class names, explanation, and remaining question in `STUDY_LOG.md` or a new note under `notes/`.

- [ ] **Step 6: Re-run the full verification before handoff**

  ```powershell
  $env:PYTHONPATH = "src"
  python -m unittest discover -s tests -v
  python -m compileall -q src tests
  ```

  Expected: the final offline suite is green; the handoff reports live checks separately with their actual status.
